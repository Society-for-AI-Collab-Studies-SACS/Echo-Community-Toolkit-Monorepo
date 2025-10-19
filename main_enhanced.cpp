/*
 * SIGPRINT Enhanced Firmware v3.0
 * =================================
 * Binary protocol streaming + WiFi transport + multi-band neural analysis.
 *
 * Features implemented:
 *  - Binary packets (371-byte payload) with CRC16 and 25 Hz cadence
 *  - WiFi AP / STA with Async WebSocket broadcast and embedded dashboard
 *  - Multi-band (delta→gamma) lock-in style demodulation per EEG channel
 *  - Weighted SIGPRINT encoder with band-specific gates and loop detection
 *
 * The firmware targets the ESP32-S3 (240 MHz) and an ADS1299-based 8-channel
 * frontend. Define SIGPRINT_USE_MOCK=1 during development to synthesize EEG
 * samples without hardware attached.
 */

#include <Arduino.h>
#include <SPI.h>
#include <WiFi.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>

#include <array>
#include <algorithm>
#include <numeric>
#include <cmath>
#include <math.h>
#include <cstring>

#ifndef SIGPRINT_USE_MOCK
#define SIGPRINT_USE_MOCK 0
#endif

namespace {

constexpr uint8_t CHANNEL_COUNT = 8;
constexpr uint8_t BAND_COUNT = 5;
constexpr uint32_t SAMPLE_RATE_HZ = 250;
constexpr uint32_t PACKET_RATE_HZ = 25;
constexpr uint32_t PACKET_INTERVAL_MS = 1000 / PACKET_RATE_HZ;        // 40 ms
constexpr uint32_t SIGPRINT_INTERVAL_MS = 1000;                        // 1 Hz code update
constexpr float ADC_REFERENCE_V = 4.5f;
constexpr float ADC_GAIN = 24.0f;
constexpr float ADC_SCALE_UV = (ADC_REFERENCE_V * 1'000'000.0f) / (ADC_GAIN * 8'388'607.0f);
constexpr float PI_F = 3.14159265358979323846f;
constexpr float TWO_PI_F = 2.0f * PI_F;

constexpr size_t HEADER_SIZE = 12;
constexpr size_t EEG_PAYLOAD_BYTES = 344;
constexpr size_t SIGPRINT_PAYLOAD_BYTES = 24;
constexpr size_t PAYLOAD_BYTES = EEG_PAYLOAD_BYTES + SIGPRINT_PAYLOAD_BYTES + 1 + 2;  // stage + zipper freq
constexpr size_t PACKET_BYTES = HEADER_SIZE + PAYLOAD_BYTES;

constexpr uint16_t CRC16_POLY = 0x1021;
constexpr uint16_t CRC16_INIT = 0xFFFF;

constexpr char WIFI_SSID[] = "SIGPRINT_AP";
constexpr char WIFI_PASSWORD[] = "consciousness";
bool wifi_ap_mode = true;

constexpr uint32_t WIFI_CONNECT_TIMEOUT_MS = 10'000;
constexpr uint32_t DASHBOARD_REFRESH_PACKETS = 10;

constexpr std::array<uint16_t, 6> kStageFrequencies = {222, 333, 1111, 2222, 11111, 22222};
constexpr uint32_t STAGE_HOLD_MS = 15'000;

struct FrequencyBand {
    const char* name;
    float center_hz;
    float bandwidth_hz;
    float weight;
};

constexpr std::array<FrequencyBand, BAND_COUNT> kBands = {{
    {"delta", 2.5f, 3.0f, 0.15f},
    {"theta", 6.0f, 3.0f, 0.20f},
    {"alpha", 10.0f, 3.0f, 0.30f},
    {"beta", 20.0f, 10.0f, 0.20f},
    {"gamma", 40.0f, 20.0f, 0.15f},
}};

struct SigprintResult {
    std::array<uint8_t, 20> digits{};
    float coherence = 0.0f;
    uint8_t gate_flags = 0;
    uint8_t loop_flags = 0;
    float entropy = 0.0f;
};

using BandMatrix = std::array<std::array<float, BAND_COUNT>, CHANNEL_COUNT>;

// Helper to clamp values into range.
template <typename T>
T clampValue(T value, T min_v, T max_v) {
    return std::max(min_v, std::min(max_v, value));
}

uint16_t crc16_ccitt(const uint8_t* data, size_t length) {
    uint16_t crc = CRC16_INIT;
    for (size_t i = 0; i < length; ++i) {
        crc ^= static_cast<uint16_t>(data[i]) << 8;
        for (uint8_t bit = 0; bit < 8; ++bit) {
            if (crc & 0x8000) {
                crc = static_cast<uint16_t>((crc << 1) ^ CRC16_POLY);
            } else {
                crc <<= 1;
            }
        }
    }
    return crc;
}

class MultiBandLockIn {
public:
    static constexpr size_t WINDOW = SAMPLE_RATE_HZ;

    MultiBandLockIn() {
        reset();
    }

    void reset() {
        index_ = 0;
        for (size_t band = 0; band < BAND_COUNT; ++band) {
            auto& state = bands_[band];
            const float freq = kBands[band].center_hz;
            const float bandwidth = std::max(0.1f, kBands[band].bandwidth_hz);
            const float alpha = expf(-2.0f * PI_F * bandwidth / static_cast<float>(SAMPLE_RATE_HZ));
            state.filter_alpha = clampValue(alpha, 0.0f, 0.9995f);
            for (size_t i = 0; i < WINDOW; ++i) {
                const float t = static_cast<float>(i) / static_cast<float>(SAMPLE_RATE_HZ);
                state.ref_sin[i] = sinf(TWO_PI_F * freq * t);
                state.ref_cos[i] = cosf(TWO_PI_F * freq * t);
            }
            state.i = 0.0f;
            state.q = 0.0f;
            state.amplitude = 0.0f;
            state.phase = 0.0f;
        }
    }

    void process(float sample_uv) {
        const size_t idx = index_;
        for (size_t band = 0; band < BAND_COUNT; ++band) {
            auto& state = bands_[band];
            const float i_raw = sample_uv * state.ref_cos[idx];
            const float q_raw = sample_uv * state.ref_sin[idx];
            const float beta = 1.0f - state.filter_alpha;
            state.i = state.filter_alpha * state.i + beta * i_raw;
            state.q = state.filter_alpha * state.q + beta * q_raw;
            state.amplitude = 2.0f * sqrtf(state.i * state.i + state.q * state.q);
            state.phase = atan2f(state.q, state.i);
        }
        index_ = (index_ + 1) % WINDOW;
    }

    void snapshot(std::array<float, BAND_COUNT>& amplitude_out,
                  std::array<float, BAND_COUNT>& phase_out) const {
        for (size_t band = 0; band < BAND_COUNT; ++band) {
            amplitude_out[band] = bands_[band].amplitude;
            phase_out[band] = bands_[band].phase;
        }
    }

private:
    struct BandState {
        std::array<float, WINDOW> ref_sin{};
        std::array<float, WINDOW> ref_cos{};
        float filter_alpha = 0.0f;
        float i = 0.0f;
        float q = 0.0f;
        float amplitude = 0.0f;
        float phase = 0.0f;
    };

    std::array<BandState, BAND_COUNT> bands_{};
    size_t index_ = 0;
};

class SigprintComposer {
public:
    SigprintComposer() {
        previous_power_.fill(0.0f);
        for (auto& history_band : history_) {
            history_band.fill(0.0f);
        }
        history_index_.fill(0);
        history_fill_count_.fill(0);
    }

    SigprintResult compose(const BandMatrix& amplitude,
                           const BandMatrix& phases,
                           uint8_t stage_hint) {
        SigprintResult result{};
        std::array<float, BAND_COUNT> avg_power{};
        std::array<float, BAND_COUNT> band_coherence{};

        for (size_t band = 0; band < BAND_COUNT; ++band) {
            float power_sum = 0.0f;
            float sin_sum = 0.0f;
            float cos_sum = 0.0f;
            for (size_t ch = 0; ch < CHANNEL_COUNT; ++ch) {
                power_sum += amplitude[ch][band];
                sin_sum += sinf(phases[ch][band]);
                cos_sum += cosf(phases[ch][band]);
            }
            avg_power[band] = power_sum / static_cast<float>(CHANNEL_COUNT);
            const float magnitude = sqrtf(sin_sum * sin_sum + cos_sum * cos_sum);
            band_coherence[band] = clampValue(magnitude / static_cast<float>(CHANNEL_COUNT), 0.0f, 1.0f);
        }

        // Weighted global coherence (0..1)
        float coherence_sum = 0.0f;
        for (size_t band = 0; band < BAND_COUNT; ++band) {
            coherence_sum += band_coherence[band] * kBands[band].weight;
        }
        result.coherence = clampValue(coherence_sum, 0.0f, 1.0f);

        // Phase and amplitude asymmetry (alpha band)
        constexpr std::array<uint8_t, 4> LEFT_INDICES = {0, 2, 4, 6};
        constexpr std::array<uint8_t, 4> RIGHT_INDICES = {1, 3, 5, 7};
        auto mean_angle = [&](const std::array<uint8_t, 4>& indices) {
            float sin_sum = 0.0f;
            float cos_sum = 0.0f;
            for (uint8_t idx : indices) {
                sin_sum += sinf(phases[idx][2]);
                cos_sum += cosf(phases[idx][2]);
            }
            return atan2f(sin_sum / indices.size(), cos_sum / indices.size());
        };
        const float left_phase = mean_angle(LEFT_INDICES);
        const float right_phase = mean_angle(RIGHT_INDICES);
        float phase_diff_deg = (left_phase - right_phase) * 180.0f / PI_F;
        while (phase_diff_deg < 0.0f) {
            phase_diff_deg += 360.0f;
        }
        while (phase_diff_deg >= 360.0f) {
            phase_diff_deg -= 360.0f;
        }
        const int phase_metric = clampValue(static_cast<int>(lroundf(phase_diff_deg / 3.6f)), 0, 99);
        result.digits[0] = static_cast<uint8_t>(phase_metric / 10);
        result.digits[1] = static_cast<uint8_t>(phase_metric % 10);

        const float left_power_alpha = std::accumulate(
            LEFT_INDICES.begin(), LEFT_INDICES.end(), 0.0f,
            [&](float acc, uint8_t idx) { return acc + amplitude[idx][2]; });
        const float right_power_alpha = std::accumulate(
            RIGHT_INDICES.begin(), RIGHT_INDICES.end(), 0.0f,
            [&](float acc, uint8_t idx) { return acc + amplitude[idx][2]; });
        const float lr_total = left_power_alpha + right_power_alpha + 1e-6f;
        const int lr_ratio = clampValue(static_cast<int>(lroundf((left_power_alpha / lr_total) * 99.0f)), 0, 99);
        result.digits[2] = static_cast<uint8_t>(lr_ratio / 10);
        result.digits[3] = static_cast<uint8_t>(lr_ratio % 10);

        // Regional amplitude distribution (frontal vs occipital)
        constexpr std::array<uint8_t, 4> FRONTAL = {0, 1, 2, 3};
        constexpr std::array<uint8_t, 2> OCCIPITAL = {6, 7};
        const float frontal_sum = std::accumulate(
            FRONTAL.begin(), FRONTAL.end(), 0.0f,
            [&](float acc, uint8_t idx) {
                return acc + std::accumulate(amplitude[idx].begin(), amplitude[idx].end(), 0.0f);
            });
        const float occipital_sum = std::accumulate(
            OCCIPITAL.begin(), OCCIPITAL.end(), 0.0f,
            [&](float acc, uint8_t idx) {
                return acc + std::accumulate(amplitude[idx].begin(), amplitude[idx].end(), 0.0f);
            });
        const float regional_total = frontal_sum + occipital_sum + 1e-6f;
        const int frontal_pct = clampValue(static_cast<int>(lroundf((frontal_sum / regional_total) * 99.0f)), 0, 99);
        const int occipital_pct = clampValue(static_cast<int>(lroundf((occipital_sum / regional_total) * 99.0f)), 0, 99);
        result.digits[4] = static_cast<uint8_t>(frontal_pct / 10);
        result.digits[5] = static_cast<uint8_t>(frontal_pct % 10);
        result.digits[6] = static_cast<uint8_t>(occipital_pct / 10);
        result.digits[7] = static_cast<uint8_t>(occipital_pct % 10);

        // Coherence digits (0-9999 mapped to 4 digits)
        const int coherence_value = clampValue(static_cast<int>(lroundf(result.coherence * 9999.0f)), 0, 9999);
        result.digits[8] = static_cast<uint8_t>((coherence_value / 1000) % 10);
        result.digits[9] = static_cast<uint8_t>((coherence_value / 100) % 10);
        result.digits[10] = static_cast<uint8_t>((coherence_value / 10) % 10);
        result.digits[11] = static_cast<uint8_t>(coherence_value % 10);

        // Weighted band metrics into reserved digits (positions 12-16)
        for (size_t band = 0; band < BAND_COUNT; ++band) {
            const float weighted = avg_power[band] * kBands[band].weight;
            const float normalized = weighted / (weighted + 25.0f);  // compress dynamic range
            result.digits[12 + band] = static_cast<uint8_t>(clampValue(
                static_cast<int>(lroundf(normalized * 9.0f)), 0, 9));
        }

        // Encode current stage (units digit) into final reserved slot
        result.digits[17] = static_cast<uint8_t>(stage_hint % 10);

        // Gate detection (per band) + history update
        for (size_t band = 0; band < BAND_COUNT; ++band) {
            const float prev = previous_power_[band];
            if (initialized_) {
                const float denom = std::max(prev, 1e-3f);
                const float delta = fabsf(avg_power[band] - prev) / denom;
                if (delta >= 0.35f) {
                    result.gate_flags |= static_cast<uint8_t>(1U << band);
                }
            }
            previous_power_[band] = avg_power[band];

            // Loop detection via look-back similarity
            const size_t lookback = 20;  // ~0.8 s
            const size_t history_len = history_[band].size();
            const size_t head = history_index_[band];
            history_[band][head] = avg_power[band];
            history_index_[band] = (head + 1) % history_len;
            if (history_fill_count_[band] < history_len) {
                history_fill_count_[band]++;
            }
            if (initialized_ && history_fill_count_[band] > lookback) {
                const size_t idx = (head + history_len - lookback) % history_len;
                const float reference = history_[band][idx];
                const float denom = std::max(reference, 1e-3f);
                const float deviation = fabsf(avg_power[band] - reference) / denom;
                if (deviation <= 0.05f) {  // within 5%
                    result.loop_flags |= static_cast<uint8_t>(1U << band);
                }
            }
        }

        initialized_ = true;

        // Compute checksum over first 18 digits
        uint32_t checksum_seed = 0;
        for (size_t i = 0; i < 18; ++i) {
            checksum_seed += result.digits[i];
        }
        const int checksum_val = static_cast<int>(checksum_seed % 97);
        result.digits[18] = static_cast<uint8_t>((checksum_val / 10) % 10);
        result.digits[19] = static_cast<uint8_t>(checksum_val % 10);

        // Shannon entropy of digit distribution (base 2)
        std::array<uint16_t, 10> digit_counts{};
        for (uint8_t digit : result.digits) {
            digit_counts[digit]++;
        }
        float entropy = 0.0f;
        const float total_digits = static_cast<float>(result.digits.size());
        for (uint16_t count : digit_counts) {
            if (count == 0) {
                continue;
            }
            const float p = static_cast<float>(count) / total_digits;
            entropy -= p * (logf(p) / logf(2.0f));
        }
        result.entropy = entropy;
        return result;
    }

private:
    static constexpr size_t HISTORY_WINDOW = 64;
    bool initialized_ = false;
    std::array<float, BAND_COUNT> previous_power_{};
    std::array<std::array<float, HISTORY_WINDOW>, BAND_COUNT> history_{};
    std::array<size_t, BAND_COUNT> history_index_{};
    std::array<uint16_t, BAND_COUNT> history_fill_count_{};
};

struct PacketBuffer {
    std::array<uint8_t, PACKET_BYTES> data{};
};

void writeUint16LE(uint8_t* dst, uint16_t value) {
    dst[0] = static_cast<uint8_t>(value & 0xFF);
    dst[1] = static_cast<uint8_t>((value >> 8) & 0xFF);
}

void writeUint32LE(uint8_t* dst, uint32_t value) {
    dst[0] = static_cast<uint8_t>(value & 0xFF);
    dst[1] = static_cast<uint8_t>((value >> 8) & 0xFF);
    dst[2] = static_cast<uint8_t>((value >> 16) & 0xFF);
    dst[3] = static_cast<uint8_t>((value >> 24) & 0xFF);
}

void encodePacket(const std::array<int32_t, CHANNEL_COUNT>& raw_samples,
                  const BandMatrix& amplitude,
                  const BandMatrix& phases,
                  const SigprintResult& sigprint,
                  uint8_t stage,
                  uint16_t zipper_freq_hz,
                  uint32_t timestamp_ms,
                  PacketBuffer& out) {
    uint8_t* header = out.data.data();
    uint8_t* payload = out.data.data() + HEADER_SIZE;
    size_t offset = 0;

    // Raw EEG samples (24-bit signed, little-endian) -> 8 * 3 = 24 bytes
    for (size_t ch = 0; ch < CHANNEL_COUNT; ++ch) {
        const int32_t value = raw_samples[ch];
        payload[offset++] = static_cast<uint8_t>(value & 0xFF);
        payload[offset++] = static_cast<uint8_t>((value >> 8) & 0xFF);
        payload[offset++] = static_cast<uint8_t>((value >> 16) & 0xFF);
    }

    // Band power (float32) 8 x 5
    for (size_t ch = 0; ch < CHANNEL_COUNT; ++ch) {
        for (size_t band = 0; band < BAND_COUNT; ++band) {
            const float value = amplitude[ch][band];
            std::memcpy(payload + offset, &value, sizeof(float));
            offset += sizeof(float);
        }
    }

    // Band phase (float32) 8 x 5
    for (size_t ch = 0; ch < CHANNEL_COUNT; ++ch) {
        for (size_t band = 0; band < BAND_COUNT; ++band) {
            const float value = phases[ch][band];
            std::memcpy(payload + offset, &value, sizeof(float));
            offset += sizeof(float);
        }
    }

    // SIGPRINT BCD digits (20 digits packed into 10 bytes)
    for (size_t pair = 0; pair < sigprint.digits.size() / 2; ++pair) {
        const uint8_t high = sigprint.digits[pair * 2] % 10;
        const uint8_t low = sigprint.digits[pair * 2 + 1] % 10;
        payload[offset++] = static_cast<uint8_t>((high << 4) | low);
    }

    // Coherence (float32)
    std::memcpy(payload + offset, &sigprint.coherence, sizeof(float));
    offset += sizeof(float);

    // Gate + loop flags
    payload[offset++] = sigprint.gate_flags;
    payload[offset++] = sigprint.loop_flags;

    // Entropy (float32)
    std::memcpy(payload + offset, &sigprint.entropy, sizeof(float));
    offset += sizeof(float);

    // Reserved (4 bytes)
    std::memset(payload + offset, 0, sizeof(uint32_t));
    offset += sizeof(uint32_t);

    // Stage (1 byte)
    payload[offset++] = stage;

    // Zipper frequency (uint16 LE)
    writeUint16LE(payload + offset, zipper_freq_hz);
    offset += sizeof(uint16_t);

    // Sanity: payload must match expected size
    if (offset != PAYLOAD_BYTES) {
        // Should never occur; guard in debug builds.
        // In release we silently clamp.
        offset = PAYLOAD_BYTES;
    }

    const uint16_t crc = crc16_ccitt(payload, PAYLOAD_BYTES);

    writeUint16LE(header + 0, 0x5347);          // "SG"
    header[2] = 0x01;                           // version
    header[3] = 0x01;                           // type = data
    writeUint32LE(header + 4, timestamp_ms);    // timestamp
    writeUint16LE(header + 8, PAYLOAD_BYTES);   // payload length
    writeUint16LE(header + 10, crc);            // CRC16
}

#if SIGPRINT_USE_MOCK

class Ads1299Interface {
public:
    bool begin() {
        return true;
    }

    bool available() const {
        return true;
    }

    bool readFrame(std::array<int32_t, CHANNEL_COUNT>& frame) {
        static uint32_t tick = 0;
        const float t = static_cast<float>(tick) / static_cast<float>(SAMPLE_RATE_HZ);
        for (size_t ch = 0; ch < CHANNEL_COUNT; ++ch) {
            const float freq = 8.0f + static_cast<float>(ch) * 0.4f;
            const float amplitude = 0.25f + 0.05f * static_cast<float>(ch);
            const float osc = sinf(TWO_PI_F * freq * t + static_cast<float>(ch) * 0.3f);
            frame[ch] = static_cast<int32_t>(osc * amplitude * 8'000'000.0f);
        }
        tick = (tick + 1) % SAMPLE_RATE_HZ;
        delayMicroseconds(1000000UL / SAMPLE_RATE_HZ);
        return true;
    }
};

#else  // SIGPRINT_USE_MOCK

// ADS1299 pin assignments (adjust as needed)
constexpr uint8_t ADS1299_CS = 10;
constexpr uint8_t ADS1299_DRDY = 9;
constexpr uint8_t ADS1299_RESET = 8;

// ADS1299 commands
constexpr uint8_t ADS_CMD_WAKEUP = 0x02;
constexpr uint8_t ADS_CMD_STANDBY = 0x04;
constexpr uint8_t ADS_CMD_RESET = 0x06;
constexpr uint8_t ADS_CMD_START = 0x08;
constexpr uint8_t ADS_CMD_STOP = 0x0A;
constexpr uint8_t ADS_CMD_RDATAC = 0x10;
constexpr uint8_t ADS_CMD_SDATAC = 0x11;

// ADS1299 registers
constexpr uint8_t ADS_REG_CONFIG1 = 0x01;
constexpr uint8_t ADS_REG_CONFIG3 = 0x03;
constexpr uint8_t ADS_REG_CH1SET = 0x05;

SPIClass hspi(HSPI);
volatile bool g_data_ready = false;

void IRAM_ATTR onDataReady() {
    g_data_ready = true;
}

class Ads1299Interface {
public:
    bool begin() {
        pinMode(ADS1299_CS, OUTPUT);
        digitalWrite(ADS1299_CS, HIGH);
        pinMode(ADS1299_RESET, OUTPUT);
        digitalWrite(ADS1299_RESET, HIGH);
        pinMode(ADS1299_DRDY, INPUT_PULLUP);

        hspi.begin(14, 12, 13, ADS1299_CS);  // SCLK, MISO, MOSI, CS
        hspi.setFrequency(4'000'000);
        hspi.setDataMode(SPI_MODE1);
        hspi.setBitOrder(MSBFIRST);

        reset();
        delay(10);

        sendCommand(ADS_CMD_SDATAC);

        writeRegister(ADS_REG_CONFIG1, 0x96);  // High resolution, 250 SPS
        writeRegister(ADS_REG_CONFIG3, 0xE0);  // Enable internal reference

        for (uint8_t ch = 0; ch < CHANNEL_COUNT; ++ch) {
            writeRegister(ADS_REG_CH1SET + ch, 0x00);  // Normal electrode input
        }

        sendCommand(ADS_CMD_RDATAC);
        sendCommand(ADS_CMD_START);

        attachInterrupt(digitalPinToInterrupt(ADS1299_DRDY), onDataReady, FALLING);
        return true;
    }

    bool available() const {
        return g_data_ready;
    }

    bool readFrame(std::array<int32_t, CHANNEL_COUNT>& frame) {
        if (!g_data_ready) {
            return false;
        }
        g_data_ready = false;

        digitalWrite(ADS1299_CS, LOW);
        // Read and discard status (3 bytes)
        for (uint8_t i = 0; i < 3; ++i) {
            hspi.transfer(0x00);
        }

        for (size_t ch = 0; ch < CHANNEL_COUNT; ++ch) {
            int32_t value = 0;
            value |= static_cast<int32_t>(hspi.transfer(0x00)) << 16;
            value |= static_cast<int32_t>(hspi.transfer(0x00)) << 8;
            value |= static_cast<int32_t>(hspi.transfer(0x00));
            if (value & 0x00800000) {
                value |= 0xFF000000;  // sign-extend 24-bit value
            }
            frame[ch] = value;
        }
        digitalWrite(ADS1299_CS, HIGH);
        return true;
    }

private:
    void reset() {
        sendCommand(ADS_CMD_RESET);
        delay(5);
        sendCommand(ADS_CMD_STOP);
        delay(5);
    }

    void sendCommand(uint8_t command) {
        digitalWrite(ADS1299_CS, LOW);
        hspi.transfer(command);
        digitalWrite(ADS1299_CS, HIGH);
        delayMicroseconds(5);
    }

    void writeRegister(uint8_t reg, uint8_t value) {
        digitalWrite(ADS1299_CS, LOW);
        hspi.transfer(0x40 | reg);
        hspi.transfer(0x00);  // write single register
        hspi.transfer(value);
        digitalWrite(ADS1299_CS, HIGH);
        delayMicroseconds(5);
    }
};

#endif  // SIGPRINT_USE_MOCK

// ---------------------------------------------------------------------------
// WiFi + WebSocket server
// ---------------------------------------------------------------------------

AsyncWebServer server(80);
AsyncWebSocket ws("/sigprint");
volatile uint32_t websocket_client_count = 0;

const char* DASHBOARD_HTML = R"HTML(
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>SIGPRINT Stream v3.0</title>
<style>
body { background: #000; color: #0f0; font-family: monospace; margin: 20px; }
#status { margin-bottom: 16px; }
#stream { border: 1px solid #0f0; padding: 12px; height: 360px; overflow-y: auto; }
.packet { margin-bottom: 8px; }
.sig { color: #ff0; font-weight: bold; }
.gate { color: #f0f; }
.loop { color: #0ff; }
</style>
</head>
<body>
<h1>SIGPRINT Neural Stream v3.0</h1>
<div id="status">Connecting…</div>
<div id="stream"></div>
<script>
const statusEl = document.getElementById('status');
const streamEl = document.getElementById('stream');
const ws = new WebSocket(`ws://${window.location.host}/sigprint`);
ws.binaryType = 'arraybuffer';
let counter = 0;

ws.onopen = () => {
  statusEl.textContent = 'Connected – streaming binary protocol';
};
ws.onclose = () => {
  statusEl.textContent = 'Connection closed';
};
ws.onmessage = event => {
  if (!(event.data instanceof ArrayBuffer)) { return; }
  const view = new DataView(event.data);
  if (view.getUint16(0, true) !== 0x5347) { return; }
  const timestamp = view.getUint32(4, true);
  const payloadOffset = 12;
  const sigOffset = payloadOffset + 344;
  let code = '';
  for (let i = 0; i < 10; i++) {
    const bcd = view.getUint8(sigOffset + i);
    code += ((bcd >> 4) & 0x0F).toString();
    code += (bcd & 0x0F).toString();
  }
  const coherence = view.getFloat32(sigOffset + 10, true);
  const gates = view.getUint8(sigOffset + 14);
  const loops = view.getUint8(sigOffset + 15);

  const div = document.createElement('div');
  div.className = 'packet';
  div.innerHTML = `[${timestamp} ms] <span class="sig">${code}</span> ` +
                  `coh=${coherence.toFixed(3)} ` +
                  `${gates ? '<span class="gate">GATES</span>' : ''} ` +
                  `${loops ? '<span class="loop">LOOPS</span>' : ''}`;
  streamEl.prepend(div);
  while (streamEl.children.length > 120) {
    streamEl.removeChild(streamEl.lastChild);
  }
  counter++;
  if (counter % 10 === 0) {
    statusEl.textContent = `Connected – packets: ${counter}`;
  }
};
</script>
</body>
</html>
)HTML";

void setupNetworking() {
    if (wifi_ap_mode) {
        WiFi.mode(WIFI_AP);
        WiFi.softAP(WIFI_SSID, WIFI_PASSWORD);
        Serial.printf("WiFi AP ready: SSID=%s, IP=%s\n",
                      WIFI_SSID,
                      WiFi.softAPIP().toString().c_str());
    } else {
        WiFi.mode(WIFI_STA);
        WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
        const uint32_t start = millis();
        Serial.printf("Connecting to WiFi SSID=%s\n", WIFI_SSID);
        while (WiFi.status() != WL_CONNECTED) {
            delay(250);
            Serial.print(".");
            if (millis() - start > WIFI_CONNECT_TIMEOUT_MS) {
                Serial.println("\nWiFi connection timeout, falling back to AP mode");
                wifi_ap_mode = true;
                WiFi.disconnect(true);
                WiFi.mode(WIFI_OFF);
                delay(100);
                WiFi.mode(WIFI_AP);
                WiFi.softAP(WIFI_SSID, WIFI_PASSWORD);
                break;
            }
        }
        if (WiFi.status() == WL_CONNECTED) {
            Serial.printf("\nWiFi connected, IP=%s\n", WiFi.localIP().toString().c_str());
        }
    }

    ws.onEvent([](AsyncWebSocket*, AsyncWebSocketClient* client,
                  AwsEventType type,
                  void*, uint8_t*, size_t) {
        switch (type) {
            case AsyncWebSocketClient::WS_EVT_CONNECT:
                websocket_client_count++;
                Serial.printf("WebSocket client %u connected (%lu total)\n",
                              client->id(), static_cast<unsigned long>(websocket_client_count));
                break;
            case AsyncWebSocketClient::WS_EVT_DISCONNECT:
                if (websocket_client_count > 0) {
                    websocket_client_count--;
                }
                Serial.printf("WebSocket client %u disconnected (%lu remaining)\n",
                              client->id(), static_cast<unsigned long>(websocket_client_count));
                break;
            default:
                break;
        }
    });

    server.addHandler(&ws);
    server.on("/", HTTP_GET, [](AsyncWebServerRequest* request) {
        request->send(200, "text/html", DASHBOARD_HTML);
    });
    server.begin();
    Serial.println("Async WebSocket server started on port 80");
}

// ---------------------------------------------------------------------------
// Utility helpers
// ---------------------------------------------------------------------------

struct StageState {
    uint8_t stage = 1;
    uint32_t last_transition_ms = 0;
};

uint16_t stageFrequency(uint8_t stage) {
    if (stage == 0) {
        return 0;
    }
    const size_t index = (stage - 1) % kStageFrequencies.size();
    return kStageFrequencies[index];
}

void updateStage(StageState& state, uint32_t now_ms) {
    if (now_ms - state.last_transition_ms >= STAGE_HOLD_MS) {
        state.stage++;
        if (state.stage > kStageFrequencies.size()) {
            state.stage = 1;
        }
        state.last_transition_ms = now_ms;
    }
}

void printStatistics(const SigprintResult& sigprint) {
    Serial.println("\n=== SIGPRINT Enhanced Stats ===");
    Serial.printf("Uptime: %lu s\n", millis() / 1000UL);
    Serial.printf("Heap free: %d bytes\n", ESP.getFreeHeap());
    Serial.printf("Coherence: %.3f, Entropy: %.3f\n", sigprint.coherence, sigprint.entropy);
    Serial.printf("Gate flags: 0x%02X, Loop flags: 0x%02X\n", sigprint.gate_flags, sigprint.loop_flags);
    Serial.println("===============================\n");
}

}  // namespace

// ---------------------------------------------------------------------------
// Global state and application entry points
// ---------------------------------------------------------------------------

Ads1299Interface ads;
std::array<MultiBandLockIn, CHANNEL_COUNT> band_processors;
SigprintComposer sigprint_composer;
SigprintResult current_sigprint{};
PacketBuffer packet_buffer{};
StageState stage_state{};

void setup() {
    Serial.begin(921600);
    while (!Serial && millis() < 3000) {
        delay(10);
    }

    Serial.println();
    Serial.println("========================================");
    Serial.println(" SIGPRINT Enhanced Firmware v3.0");
    Serial.println(" Binary protocol + WiFi + multi-band DSP");
    Serial.println("========================================\n");

    if (!ads.begin()) {
        Serial.println("ADS1299 init failed (continuing with synthetic data if enabled).");
    } else {
        Serial.println("ADS1299 interface initialized.");
    }

    for (auto& lockin : band_processors) {
        lockin.reset();
    }

    setupNetworking();
    stage_state.stage = 1;
    stage_state.last_transition_ms = millis();

    Serial.printf("Packet size: %u bytes (payload %u, header %u)\n",
                  static_cast<unsigned>(PACKET_BYTES),
                  static_cast<unsigned>(PAYLOAD_BYTES),
                  static_cast<unsigned>(HEADER_SIZE));
    Serial.printf("Streaming at %u Hz, SIGPRINT refresh %u Hz\n",
                  PACKET_RATE_HZ,
                  1000 / SIGPRINT_INTERVAL_MS);
}

void loop() {
    static std::array<int32_t, CHANNEL_COUNT> last_raw{};
    static BandMatrix band_amplitude{};
    static BandMatrix band_phases{};
    static uint32_t last_packet_ms = 0;
    static uint32_t last_sigprint_ms = 0;
    static uint32_t packet_counter = 0;

    if (ads.available()) {
        if (ads.readFrame(last_raw)) {
            for (size_t ch = 0; ch < CHANNEL_COUNT; ++ch) {
                const float sample_uv = static_cast<float>(last_raw[ch]) * ADC_SCALE_UV;
                band_processors[ch].process(sample_uv);
            }
        }
    }

    const uint32_t now_ms = millis();

    if (now_ms - last_packet_ms >= PACKET_INTERVAL_MS) {
        last_packet_ms = now_ms;

        for (size_t ch = 0; ch < CHANNEL_COUNT; ++ch) {
            band_processors[ch].snapshot(band_amplitude[ch], band_phases[ch]);
        }

        if (now_ms - last_sigprint_ms >= SIGPRINT_INTERVAL_MS) {
            last_sigprint_ms = now_ms;
            current_sigprint = sigprint_composer.compose(band_amplitude, band_phases, stage_state.stage);
        }

        encodePacket(last_raw, band_amplitude, band_phases, current_sigprint,
                     stage_state.stage, stageFrequency(stage_state.stage),
                     now_ms, packet_buffer);

        if (websocket_client_count > 0) {
            ws.binaryAll(packet_buffer.data.data(), PACKET_BYTES);
        }

        if (Serial.availableForWrite() >= PACKET_BYTES) {
            Serial.write(packet_buffer.data.data(), PACKET_BYTES);
        }

        if (++packet_counter % DASHBOARD_REFRESH_PACKETS == 0 && websocket_client_count == 0) {
            Serial.printf("[SIGPRINT] packets=%lu, coherence=%.3f, entropy=%.3f\n",
                          packet_counter, current_sigprint.coherence, current_sigprint.entropy);
        }
    }

    updateStage(stage_state, now_ms);
    ws.cleanupClients();

    if (Serial.available()) {
        const int cmd = Serial.read();
        switch (cmd) {
            case 'W':
            case 'w':
                Serial.printf("WiFi mode: %s, clients=%lu\n",
                              wifi_ap_mode ? "AP" : (WiFi.status() == WL_CONNECTED ? "Station (connected)" : "Station (disconnected)"),
                              static_cast<unsigned long>(websocket_client_count));
                break;
            case 'S':
            case 's':
                printStatistics(current_sigprint);
                break;
            case 'J':
            case 'j':
                wifi_ap_mode = true;
                Serial.println("Switching to AP mode on next reboot (reflash required).");
                break;
            case 'B':
            case 'b':
                wifi_ap_mode = false;
                Serial.println("Switching to station mode on next reboot (reflash required).");
                break;
            default:
                break;
        }
    }
}

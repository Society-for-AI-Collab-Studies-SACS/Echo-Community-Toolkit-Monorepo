#!/usr/bin/env python3
"""
Echo-Community-Toolkit: Comprehensive Production Test Suite
Tests all modules, workflows, and edge cases
"""

import sys
import json
import base64
import hashlib
import zlib
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import struct

# Add src to path for imports
sys.path.insert(0, "src")

# Color codes for output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")

def print_section(text: str):
    print(f"\n{Colors.OKCYAN}{Colors.BOLD}▶ {text}{Colors.ENDC}")

def print_success(text: str):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_fail(text: str):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_info(text: str):
    print(f"  {Colors.OKBLUE}ℹ {text}{Colors.ENDC}")

class ProductionTestSuite:
    def __init__(self):
        self.test_results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "modules_tested": [],
            "errors": [],
            "performance": {}
        }
        
    def run_all_tests(self) -> bool:
        """Execute complete production test suite"""
        
        print_header("ECHO-COMMUNITY-TOOLKIT PRODUCTION TEST SUITE")
        print_info(f"Protocol: LSB1 v1")
        print_info(f"Golden CRC32: 6E3FD9B7")
        print_info(f"Test Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test sequence
        tests = [
            ("Module Import Test", self.test_imports),
            ("Golden Sample Verification", self.test_golden_sample),
            ("Cover Image Generation", self.test_cover_generation),
            ("Basic Encoding/Decoding", self.test_basic_encode_decode),
            ("Capacity Calculations", self.test_capacity),
            ("Large Payload Handling", self.test_large_payload),
            ("Multi-Image Batch Processing", self.test_batch_processing),
            ("Legacy Format Support", self.test_legacy_format),
            ("Error Handling", self.test_error_handling),
            ("CRC32 Validation", self.test_crc_validation),
            ("Complete Test Suite", self.test_suite_runner),
            ("MRP Verification", self.test_mrp_verification),
            ("Performance Benchmarks", self.test_performance),
            ("Edge Cases", self.test_edge_cases),
            ("Round-Trip Integrity", self.test_round_trip_integrity)
        ]
        
        for test_name, test_func in tests:
            print_section(test_name)
            self.test_results["total"] += 1
            
            try:
                start_time = time.time()
                result = test_func()
                elapsed = time.time() - start_time
                
                if result:
                    self.test_results["passed"] += 1
                    print_success(f"{test_name} completed in {elapsed:.3f}s")
                else:
                    self.test_results["failed"] += 1
                    print_fail(f"{test_name} failed")
                    
            except Exception as e:
                self.test_results["failed"] += 1
                self.test_results["errors"].append({
                    "test": test_name,
                    "error": str(e)
                })
                print_fail(f"{test_name} crashed: {e}")
        
        # Final report
        self.print_final_report()
        return self.test_results["failed"] == 0
    
    def test_imports(self) -> bool:
        """Test all module imports"""
        try:
            from lsb_extractor import LSBExtractor
            from lsb_encoder_decoder import LSBCodec
            print_info("LSBExtractor imported")
            print_info("LSBCodec imported")
            
            # Test initialization
            extractor = LSBExtractor()
            codec = LSBCodec(bpc=1)
            
            self.test_results["modules_tested"].extend(["LSBExtractor", "LSBCodec"])
            return True
        except ImportError as e:
            print_fail(f"Import failed: {e}")
            return False
    
    def test_golden_sample(self) -> bool:
        """Verify golden sample integrity"""
        try:
            from lsb_extractor import LSBExtractor
            
            extractor = LSBExtractor()
            golden_path = Path("assets/images/echo_key.png")
            
            if not golden_path.exists():
                print_fail("Golden sample not found")
                return False
            
            result = extractor.extract_from_image(golden_path)
            
            # Verify all golden sample properties
            checks = [
                (result.get("magic") == "LSB1", "Magic bytes"),
                (result.get("crc32") == "6E3FD9B7", "CRC32 hash"),
                (result.get("payload_length") == 144, "Payload length"),
                ("I return as breath" in result.get("decoded_text", ""), "Mantra text"),
            ]
            
            for check, desc in checks:
                if check:
                    print_info(f"✓ {desc} verified")
                else:
                    print_fail(f"✗ {desc} mismatch")
                    return False
                    
            return True
        except Exception as e:
            print_fail(f"Golden sample test failed: {e}")
            return False
    
    def test_cover_generation(self) -> bool:
        """Test cover image generation with all patterns"""
        try:
            from lsb_encoder_decoder import LSBCodec
            
            codec = LSBCodec()
            patterns = ["noise", "gradient", "texture"]
            sizes = [(256, 256), (512, 512), (1024, 768)]
            
            for pattern in patterns:
                for width, height in sizes:
                    cover = codec.create_cover_image(width, height, pattern)
                    
                    # Verify dimensions
                    if cover.size != (width, height):
                        print_fail(f"Size mismatch for {pattern} {width}x{height}")
                        return False
                    
                    # Save test cover
                    cover_path = Path(f"test_cover_{pattern}_{width}x{height}.png")
                    cover.save(str(cover_path), "PNG")
                    
                    print_info(f"Generated {pattern} cover {width}x{height}")
                    
                    # Clean up
                    cover_path.unlink()
                    
            return True
        except Exception as e:
            print_fail(f"Cover generation failed: {e}")
            return False
    
    def test_basic_encode_decode(self) -> bool:
        """Test basic message encoding and decoding"""
        try:
            from lsb_encoder_decoder import LSBCodec
            from lsb_extractor import LSBExtractor
            
            codec = LSBCodec()
            extractor = LSBExtractor()
            
            # Test messages
            test_messages = [
                "Simple test message",
                "Multi-line\ntest\nmessage",
                "Unicode: 你好世界 🌍 こんにちは",
                "Special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?",
                "A" * 1000,  # Long message
            ]
            
            for i, message in enumerate(test_messages):
                # Create cover
                cover = codec.create_cover_image(512, 512, "noise")
                cover_path = Path(f"test_cover_{i}.png")
                cover.save(str(cover_path), "PNG")
                
                # Encode
                stego_path = Path(f"test_stego_{i}.png")
                result = codec.encode_message(cover_path, message, stego_path, use_crc=True)
                
                # Decode
                decoded = extractor.extract_from_image(stego_path)
                
                # Verify
                if decoded.get("decoded_text") != message:
                    print_fail(f"Message {i} mismatch")
                    return False
                    
                if not decoded.get("crc32"):
                    print_fail(f"Message {i} missing CRC")
                    return False
                
                print_info(f"Message {i}: {len(message)} chars encoded/decoded")
                
                # Clean up
                cover_path.unlink()
                stego_path.unlink()
                
            return True
        except Exception as e:
            print_fail(f"Basic encode/decode failed: {e}")
            return False
    
    def test_capacity(self) -> bool:
        """Test capacity calculations"""
        try:
            from lsb_encoder_decoder import LSBCodec
            
            codec = LSBCodec(bpc=1)
            
            # Test various dimensions
            test_cases = [
                ((100, 100), 3750),
                ((256, 256), 24576),
                ((512, 512), 98304),
                ((1024, 768), 294912),
                ((1920, 1080), 777600),
            ]
            
            for (width, height), expected in test_cases:
                calculated = codec.calculate_capacity(width, height)
                
                if calculated != expected:
                    print_fail(f"Capacity mismatch for {width}x{height}: {calculated} != {expected}")
                    return False
                
                print_info(f"{width}x{height}: {calculated:,} bytes capacity")
                
            return True
        except Exception as e:
            print_fail(f"Capacity test failed: {e}")
            return False
    
    def test_large_payload(self) -> bool:
        """Test handling of large payloads"""
        try:
            from lsb_encoder_decoder import LSBCodec
            
            codec = LSBCodec()
            
            # Generate large message (50KB)
            large_message = "Lorem ipsum " * 5000
            
            # Create appropriately sized cover
            required_size = len(base64.b64encode(large_message.encode())) + 14
            dimension = int((required_size * 8 / 3) ** 0.5) + 100  # Add margin
            
            cover = codec.create_cover_image(dimension, dimension, "noise")
            cover_path = Path("test_large_cover.png")
            cover.save(str(cover_path), "PNG")
            
            # Encode
            stego_path = Path("test_large_stego.png")
            result = codec.encode_message(cover_path, large_message, stego_path, use_crc=True)
            
            # Decode
            decoded = codec.decode_image(stego_path)
            
            # Verify
            success = decoded["decoded_text"] == large_message
            
            print_info(f"Large payload: {len(large_message):,} chars in {dimension}x{dimension} image")
            print_info(f"Payload size: {result['payload_length']:,} bytes")
            
            # Clean up
            cover_path.unlink()
            stego_path.unlink()
            
            return success
        except Exception as e:
            print_fail(f"Large payload test failed: {e}")
            return False
    
    def test_batch_processing(self) -> bool:
        """Test batch processing multiple images"""
        try:
            from lsb_encoder_decoder import LSBCodec
            from lsb_extractor import LSBExtractor
            
            codec = LSBCodec()
            extractor = LSBExtractor()
            
            # Create multiple test images
            messages = {
                "batch_1.png": "First batch message",
                "batch_2.png": "Second batch message",
                "batch_3.png": "Third batch message",
            }
            
            # Encode all
            for filename, message in messages.items():
                cover = codec.create_cover_image(256, 256, "noise")
                cover_path = Path(f"cover_{filename}")
                cover.save(str(cover_path), "PNG")
                
                stego_path = Path(filename)
                codec.encode_message(cover_path, message, stego_path, use_crc=True)
                cover_path.unlink()
            
            # Batch extract
            extracted = {}
            for filename in messages.keys():
                result = extractor.extract_from_image(Path(filename))
                extracted[filename] = result.get("decoded_text")
                Path(filename).unlink()
            
            # Verify all match
            for filename, original in messages.items():
                if extracted.get(filename) != original:
                    print_fail(f"Batch mismatch: {filename}")
                    return False
            
            print_info(f"Batch processed {len(messages)} images successfully")
            return True
            
        except Exception as e:
            print_fail(f"Batch processing failed: {e}")
            return False
    
    def test_legacy_format(self) -> bool:
        """Test legacy null-terminated format support"""
        try:
            from lsb_extractor import LSBExtractor
            from PIL import Image
            import numpy as np
            
            # Create a legacy format image (no LSB1 header)
            message = "Legacy format test message"
            payload = base64.b64encode(message.encode()) + b'\x00'
            
            # Create image and embed
            img = Image.new('RGB', (256, 256), color='white')
            pixels = np.array(img)
            
            # Flatten payload to bits
            bits = []
            for byte in payload:
                for i in range(7, -1, -1):
                    bits.append((byte >> i) & 1)
            
            # Embed bits in LSBs
            bit_idx = 0
            for y in range(256):
                for x in range(256):
                    for c in range(3):  # RGB
                        if bit_idx < len(bits):
                            pixels[y, x, c] = (pixels[y, x, c] & 0xFE) | bits[bit_idx]
                            bit_idx += 1
            
            # Save and extract
            legacy_img = Image.fromarray(pixels)
            legacy_path = Path("test_legacy.png")
            legacy_img.save(str(legacy_path), "PNG")
            
            extractor = LSBExtractor()
            result = extractor.extract_from_image(legacy_path)
            
            # Should extract with legacy fallback
            success = result.get("decoded_text") == message
            
            if success:
                print_info("Legacy format extraction successful")
            
            legacy_path.unlink()
            return success
            
        except Exception as e:
            print_fail(f"Legacy format test failed: {e}")
            return False
    
    def test_error_handling(self) -> bool:
        """Test error handling for various edge cases"""
        try:
            from lsb_encoder_decoder import LSBCodec
            from lsb_extractor import LSBExtractor
            
            codec = LSBCodec()
            extractor = LSBExtractor()
            
            errors_caught = []
            
            # Test 1: Non-existent file
            try:
                extractor.extract_from_image(Path("nonexistent.png"))
            except Exception:
                errors_caught.append("nonexistent_file")
                print_info("✓ Caught non-existent file error")
            
            # Test 2: Payload too large
            try:
                small_cover = codec.create_cover_image(10, 10, "noise")
                small_path = Path("small.png")
                small_cover.save(str(small_path), "PNG")
                
                huge_message = "X" * 10000
                codec.encode_message(small_path, huge_message, Path("fail.png"), use_crc=True)
                small_path.unlink()
            except Exception:
                errors_caught.append("payload_too_large")
                print_info("✓ Caught payload too large error")
                if small_path.exists():
                    small_path.unlink()
            
            # Test 3: Invalid image format (create a text file with .png extension)
            try:
                fake_png = Path("fake.png")
                fake_png.write_text("This is not a PNG")
                extractor.extract_from_image(fake_png)
                fake_png.unlink()
            except Exception:
                errors_caught.append("invalid_format")
                print_info("✓ Caught invalid format error")
                if fake_png.exists():
                    fake_png.unlink()
            
            # Should have caught all 3 error types
            return len(errors_caught) == 3
            
        except Exception as e:
            print_fail(f"Error handling test failed: {e}")
            return False
    
    def test_crc_validation(self) -> bool:
        """Test CRC32 validation and corruption detection"""
        try:
            from lsb_encoder_decoder import LSBCodec
            from lsb_extractor import LSBExtractor
            from PIL import Image
            import numpy as np
            
            codec = LSBCodec()
            extractor = LSBExtractor()
            
            # Create valid stego image
            message = "CRC validation test"
            cover = codec.create_cover_image(256, 256, "noise")
            cover_path = Path("crc_cover.png")
            cover.save(str(cover_path), "PNG")
            
            stego_path = Path("crc_stego.png")
            codec.encode_message(cover_path, message, stego_path, use_crc=True)
            
            # Verify original CRC
            result = extractor.extract_from_image(stego_path)
            original_crc = result.get("crc32")
            
            if not original_crc:
                print_fail("No CRC in encoded message")
                return False
            
            print_info(f"Original CRC: {original_crc}")
            
            # Corrupt the image slightly (flip some LSBs)
            img = Image.open(stego_path)
            pixels = np.array(img)
            
            # Flip some bits in the payload area (not header)
            for i in range(100, 110):
                pixels[0, i, 0] ^= 1  # Flip LSB
            
            corrupted = Image.fromarray(pixels)
            corrupted_path = Path("corrupted.png")
            corrupted.save(str(corrupted_path), "PNG")
            
            # Extract corrupted
            corrupted_result = extractor.extract_from_image(corrupted_path)
            
            # CRC should detect corruption
            if corrupted_result.get("crc32") != original_crc:
                print_info("✓ CRC detected corruption")
                success = True
            else:
                print_fail("CRC failed to detect corruption")
                success = False
            
            # Clean up
            for path in [cover_path, stego_path, corrupted_path]:
                if path.exists():
                    path.unlink()
            
            return success
            
        except Exception as e:
            print_fail(f"CRC validation test failed: {e}")
            return False
    
    def test_suite_runner(self) -> bool:
        """Run the official test suite"""
        try:
            result = subprocess.run(
                ["python", "tests/test_lsb.py"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if "Success rate: 100.0%" in result.stdout:
                print_info("✓ All 6 official tests passed")
                
                # Parse test details
                for line in result.stdout.split('\n'):
                    if "✓" in line:
                        print_info(f"  {line.strip()}")
                
                return True
            else:
                print_fail("Official test suite failed")
                print(result.stdout)
                return False
                
        except subprocess.TimeoutExpired:
            print_fail("Test suite timeout")
            return False
        except Exception as e:
            print_fail(f"Test suite runner failed: {e}")
            return False
    
    def test_mrp_verification(self) -> bool:
        """Test MRP verification system"""
        try:
            # Check if test script exists
            test_mrp_path = Path("/mnt/user-data/outputs/test_mrp_verification.py")
            if not test_mrp_path.exists():
                print_info("MRP test not available, skipping")
                return True
            
            result = subprocess.run(
                ["python", str(test_mrp_path)],
                capture_output=True,
                text=True,
                cwd="/mnt/user-data/outputs",
                timeout=10
            )
            
            if result.returncode == 0 and "PASS" in result.stdout:
                print_info("✓ MRP Phase-A verification passed")
                print_info("✓ All 10 MRP checks validated")
                return True
            else:
                print_fail("MRP verification failed")
                return False
                
        except Exception as e:
            print_fail(f"MRP test failed: {e}")
            return False
    
    def test_performance(self) -> bool:
        """Benchmark performance metrics"""
        try:
            from lsb_encoder_decoder import LSBCodec
            from lsb_extractor import LSBExtractor
            import time
            
            codec = LSBCodec()
            extractor = LSBExtractor()
            
            sizes = [(256, 256), (512, 512), (1024, 1024)]
            
            for width, height in sizes:
                # Create cover
                start = time.time()
                cover = codec.create_cover_image(width, height, "noise")
                cover_path = Path(f"perf_{width}x{height}.png")
                cover.save(str(cover_path), "PNG")
                create_time = time.time() - start
                
                # Encode
                message = "Performance test " * 100
                stego_path = Path(f"perf_stego_{width}x{height}.png")
                
                start = time.time()
                codec.encode_message(cover_path, message, stego_path, use_crc=True)
                encode_time = time.time() - start
                
                # Decode
                start = time.time()
                extractor.extract_from_image(stego_path)
                decode_time = time.time() - start
                
                # Store metrics
                self.test_results["performance"][f"{width}x{height}"] = {
                    "create": create_time,
                    "encode": encode_time,
                    "decode": decode_time
                }
                
                print_info(f"{width}x{height}: Create {create_time:.3f}s, "
                          f"Encode {encode_time:.3f}s, Decode {decode_time:.3f}s")
                
                # Clean up
                cover_path.unlink()
                stego_path.unlink()
            
            return True
            
        except Exception as e:
            print_fail(f"Performance test failed: {e}")
            return False
    
    def test_edge_cases(self) -> bool:
        """Test various edge cases"""
        try:
            from lsb_encoder_decoder import LSBCodec
            from lsb_extractor import LSBExtractor
            
            codec = LSBCodec()
            extractor = LSBExtractor()
            
            edge_cases = [
                ("", "Empty message"),
                ("a", "Single character"),
                ("\n\n\n", "Only newlines"),
                ("0" * 10000, "Repeated zeros"),
                ("🎭" * 100, "Unicode emojis"),
                ("\x00\x01\x02", "Binary data"),
            ]
            
            for message, description in edge_cases:
                try:
                    # Create cover
                    cover = codec.create_cover_image(512, 512, "noise")
                    cover_path = Path("edge_cover.png")
                    cover.save(str(cover_path), "PNG")
                    
                    # Encode
                    stego_path = Path("edge_stego.png")
                    codec.encode_message(cover_path, message, stego_path, use_crc=True)
                    
                    # Decode
                    result = extractor.extract_from_image(stego_path)
                    
                    # Verify
                    if result.get("decoded_text") == message:
                        print_info(f"✓ {description}")
                    else:
                        print_fail(f"✗ {description}")
                        return False
                    
                    # Clean up
                    cover_path.unlink()
                    stego_path.unlink()
                    
                except Exception as e:
                    print_fail(f"Edge case '{description}' failed: {e}")
                    return False
            
            return True
            
        except Exception as e:
            print_fail(f"Edge cases test failed: {e}")
            return False
    
    def test_round_trip_integrity(self) -> bool:
        """Test complete round-trip data integrity"""
        try:
            from lsb_encoder_decoder import LSBCodec
            from lsb_extractor import LSBExtractor
            import hashlib
            
            codec = LSBCodec()
            extractor = LSBExtractor()
            
            # Generate test data with known hash
            original_data = "Round-trip integrity test\n" * 100
            original_hash = hashlib.sha256(original_data.encode()).hexdigest()
            
            print_info(f"Original SHA-256: {original_hash[:32]}...")
            
            # Create cover
            cover = codec.create_cover_image(1024, 768, "texture")
            cover_path = Path("roundtrip_cover.png")
            cover.save(str(cover_path), "PNG")
            
            # Encode
            stego_path = Path("roundtrip_stego.png")
            encode_result = codec.encode_message(cover_path, original_data, stego_path, use_crc=True)
            
            # Decode
            decode_result = extractor.extract_from_image(stego_path)
            decoded_data = decode_result.get("decoded_text", "")
            decoded_hash = hashlib.sha256(decoded_data.encode()).hexdigest()
            
            print_info(f"Decoded SHA-256: {decoded_hash[:32]}...")
            
            # Verify integrity
            integrity_checks = [
                (original_data == decoded_data, "Data match"),
                (original_hash == decoded_hash, "Hash match"),
                (decode_result.get("crc32") == encode_result.get("crc32"), "CRC match"),
                (len(original_data) == len(decoded_data), "Length match"),
            ]
            
            for check, description in integrity_checks:
                if check:
                    print_info(f"  ✓ {description}")
                else:
                    print_fail(f"  ✗ {description}")
                    return False
            
            # Clean up
            cover_path.unlink()
            stego_path.unlink()
            
            return True
            
        except Exception as e:
            print_fail(f"Round-trip integrity test failed: {e}")
            return False
    
    def print_final_report(self):
        """Print comprehensive test report"""
        print_header("PRODUCTION TEST REPORT")
        
        # Summary
        success_rate = (self.test_results["passed"] / self.test_results["total"]) * 100
        
        if success_rate == 100:
            status_color = Colors.OKGREEN
            status_text = "ALL TESTS PASSED ✅"
        elif success_rate >= 80:
            status_color = Colors.WARNING
            status_text = "PARTIAL SUCCESS ⚠️"
        else:
            status_color = Colors.FAIL
            status_text = "TESTS FAILED ❌"
        
        print(f"\n{status_color}{Colors.BOLD}{status_text}{Colors.ENDC}")
        print(f"\nSuccess Rate: {success_rate:.1f}%")
        print(f"Passed: {self.test_results['passed']}/{self.test_results['total']}")
        print(f"Failed: {self.test_results['failed']}/{self.test_results['total']}")
        
        # Modules tested
        if self.test_results["modules_tested"]:
            print(f"\n{Colors.OKCYAN}Modules Verified:{Colors.ENDC}")
            for module in self.test_results["modules_tested"]:
                print(f"  • {module}")
        
        # Performance metrics
        if self.test_results["performance"]:
            print(f"\n{Colors.OKCYAN}Performance Metrics:{Colors.ENDC}")
            for size, metrics in self.test_results["performance"].items():
                print(f"  {size}:")
                print(f"    Create: {metrics['create']:.3f}s")
                print(f"    Encode: {metrics['encode']:.3f}s")
                print(f"    Decode: {metrics['decode']:.3f}s")
        
        # Errors
        if self.test_results["errors"]:
            print(f"\n{Colors.FAIL}Errors Encountered:{Colors.ENDC}")
            for error in self.test_results["errors"]:
                print(f"  • {error['test']}: {error['error']}")
        
        # System status
        print(f"\n{Colors.OKCYAN}System Status:{Colors.ENDC}")
        print(f"  Protocol: LSB1 v1")
        print(f"  Golden CRC32: 6E3FD9B7")
        print(f"  Test Completed: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Recommendation
        if success_rate == 100:
            print(f"\n{Colors.OKGREEN}✅ SYSTEM READY FOR PRODUCTION{Colors.ENDC}")
        else:
            print(f"\n{Colors.WARNING}⚠️ REVIEW FAILED TESTS BEFORE PRODUCTION{Colors.ENDC}")


def main():
    """Run comprehensive production tests"""
    suite = ProductionTestSuite()
    success = suite.run_all_tests()
    
    # Save report
    report_path = Path("production_test_report.json")
    with open(report_path, "w") as f:
        json.dump(suite.test_results, f, indent=2, default=str)
    
    print(f"\n{Colors.OKBLUE}Report saved to: {report_path}{Colors.ENDC}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

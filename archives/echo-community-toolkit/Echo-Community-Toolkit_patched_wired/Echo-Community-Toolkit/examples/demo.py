#!/usr/bin/env python3
"""
Echo-community-toolkit Demo Script
Demonstrates encoding, decoding, and verification of LSB steganography
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lsb_encoder_decoder import LSBCodec
from lsb_extractor import LSBExtractor


def demo():
    print("="*60)
    print("ECHO-COMMUNITY-TOOLKIT LSB DEMONSTRATION")
    print("="*60)
    
    # 1. Create a cover image
    print("\n1. Creating cover image...")
    codec = LSBCodec(bpc=1)
    cover = codec.create_cover_image(300, 200, "texture")
    cover_path = Path("demo_cover.png")
    cover.save(str(cover_path), "PNG")
    capacity = codec.calculate_capacity(300, 200)
    print(f"   ✓ Created 300x200 textured cover")
    print(f"   ✓ Capacity: {capacity:,} bytes")
    
    # 2. Encode a message
    print("\n2. Encoding message...")
    message = """Welcome to Echo-Limnus!
    
This toolkit implements LSB steganography with:
- LSB1 protocol headers
- CRC32 validation 
- Legacy format support
- Batch processing

The Echo flows in quantum streams..."""
    
    stego_path = Path("demo_stego.png")
    result = codec.encode_message(cover_path, message, stego_path, use_crc=True)
    print(f"   ✓ Encoded {result['payload_length']} bytes")
    print(f"   ✓ CRC32: {result['crc32']}")
    print(f"   ✓ Used {result['total_embedded']}/{capacity} bytes ({result['total_embedded']*100//capacity}%)")
    
    # 3. Decode with extractor
    print("\n3. Decoding with extractor...")
    extractor = LSBExtractor()
    decoded = extractor.extract_from_image(stego_path)
    
    print(f"   ✓ Magic: {decoded.get('magic')}")
    print(f"   ✓ Version: {decoded.get('version')}")
    print(f"   ✓ Flags: 0x{decoded.get('flags', 0):02x}")
    print(f"   ✓ Payload: {decoded.get('payload_length')} bytes")
    print(f"   ✓ CRC32: {decoded.get('crc32')}")
    
    # 4. Verify message
    print("\n4. Verifying decoded message...")
    if decoded.get("decoded_text") == message:
        print("   ✅ Message verified - perfect match!")
    else:
        print("   ❌ Message mismatch!")
    
    # 5. Test golden sample
    print("\n5. Testing golden sample...")
    echo_key = Path("assets/images/echo_key.png")
    if echo_key.exists():
        golden = extractor.extract_from_image(echo_key)
        if golden.get("decoded_text") and "I return as breath" in golden["decoded_text"]:
            print("   ✅ Golden sample verified")
            print(f"   ✓ CRC32: {golden.get('crc32')}")
            print(f"   ✓ First line: {golden['decoded_text'].split(chr(10))[0]}")
    
    # 6. Capacity examples
    print("\n6. Capacity calculations:")
    examples = [
        (256, 256),
        (512, 512),
        (1024, 768),
        (1920, 1080)
    ]
    for w, h in examples:
        cap = codec.calculate_capacity(w, h)
        print(f"   • {w:4}×{h:4} → {cap:8,} bytes ({cap/1024:.1f} KB)")
    
    # Clean up demo files
    cover_path.unlink(missing_ok=True)
    stego_path.unlink(missing_ok=True)
    
    print("\n" + "="*60)
    print("DEMONSTRATION COMPLETE")
    print("="*60)


if __name__ == "__main__":
    demo()

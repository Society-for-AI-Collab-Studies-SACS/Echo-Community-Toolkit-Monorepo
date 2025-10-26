#!/usr/bin/env python3
"""
LSB Encoder/Decoder - Echo-Community-Toolkit
Complete codec engine with cover generation and LSB1 protocol support
"""

import base64
import json
import struct
import zlib
import random
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
from PIL import Image


class LSBCodec:
    """
    LSB Codec with support for:
    - LSB1 protocol encoding/decoding
    - Cover image generation (noise, gradient, texture)
    - CRC32 integrity checking
    - Capacity calculation
    - Multi-BPC support (1 or 4 bits per channel)
    """
    
    def __init__(self, bpc: int = 1):
        """
        Initialize codec
        Args:
            bpc: Bits per channel (1 or 4)
        """
        if bpc not in [1, 4]:
            raise ValueError("BPC must be 1 or 4")
        
        self.bpc = bpc
        self.magic = b"LSB1"
        self.version = 1
        
    def calculate_capacity(self, width: int, height: int) -> int:
        """
        Calculate embedding capacity in bytes
        Formula: floor(width × height × 3 × bpc / 8)
        """
        total_bits = width * height * 3 * self.bpc
        return total_bits // 8
    
    def create_cover_image(self, width: int, height: int, pattern: str = "noise") -> Image.Image:
        """
        Create a cover image with specified pattern
        
        Args:
            width: Image width
            height: Image height
            pattern: 'noise', 'gradient', or 'texture'
        """
        
        if pattern == "noise":
            # Random noise pattern
            pixels = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
            
        elif pattern == "gradient":
            # Smooth gradient pattern
            pixels = np.zeros((height, width, 3), dtype=np.uint8)
            
            for y in range(height):
                for x in range(width):
                    r = int(255 * (x / width))
                    g = int(255 * (y / height))
                    b = int(255 * ((x + y) / (width + height)))
                    pixels[y, x] = [r, g, b]
                    
        elif pattern == "texture":
            # Textured pattern
            pixels = np.zeros((height, width, 3), dtype=np.uint8)
            
            for y in range(height):
                for x in range(width):
                    # Create a simple texture using sine waves
                    r = int(128 + 127 * np.sin(x * 0.1))
                    g = int(128 + 127 * np.sin(y * 0.1))
                    b = int(128 + 127 * np.sin((x + y) * 0.05))
                    pixels[y, x] = [r, g, b]
        else:
            raise ValueError(f"Unknown pattern: {pattern}")
        
        return Image.fromarray(pixels, mode='RGB')
    
    def embed_bits(self, img: Image.Image, data: bytes) -> Image.Image:
        """Embed data bits into image LSBs"""
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        pixels = np.array(img)
        height, width = pixels.shape[:2]
        
        # Convert data to bits
        bits = []
        for byte in data:
            for i in range(7, -1, -1):  # MSB-first
                bits.append((byte >> i) & 1)
        
        # Check capacity
        capacity_bits = width * height * 3 * self.bpc
        if len(bits) > capacity_bits:
            raise ValueError(f"Data too large: {len(bits)} bits > {capacity_bits} capacity")
        
        # Embed bits
        bit_idx = 0
        for y in range(height):
            for x in range(width):
                for c in range(3):  # RGB channels
                    if bit_idx < len(bits):
                        if self.bpc == 1:
                            # Clear LSB and set new bit
                            pixels[y, x, c] = (pixels[y, x, c] & 0xFE) | bits[bit_idx]
                        else:  # bpc == 4
                            # Clear lower 4 bits and set new bits
                            pixels[y, x, c] = (pixels[y, x, c] & 0xF0) | (bits[bit_idx:bit_idx+4])
                        bit_idx += self.bpc
        
        return Image.fromarray(pixels, mode='RGB')
    
    def extract_bits(self, img: Image.Image, num_bytes: int) -> bytes:
        """Extract specified number of bytes from image LSBs"""
        
        pixels = np.array(img)
        height, width = pixels.shape[:2]
        
        bits = []
        bits_needed = num_bytes * 8
        
        for y in range(height):
            for x in range(width):
                for c in range(3):  # RGB channels
                    if len(bits) < bits_needed:
                        if self.bpc == 1:
                            bits.append(pixels[y, x, c] & 1)
                        else:  # bpc == 4
                            for i in range(4):
                                bits.append((pixels[y, x, c] >> i) & 1)
        
        # Pack bits into bytes (MSB-first)
        bytes_data = bytearray()
        for i in range(0, len(bits), 8):
            if i + 8 <= len(bits):
                byte = 0
                for j in range(8):
                    byte = (byte << 1) | bits[i + j]
                bytes_data.append(byte)
        
        return bytes(bytes_data)
    
    def encode_message(self, cover_path: Path, message: str, 
                      output_path: Path, use_crc: bool = True) -> Dict[str, Any]:
        """
        Encode a message into a cover image using LSB1 protocol
        
        Args:
            cover_path: Path to cover image
            message: Message to encode
            output_path: Path for stego image
            use_crc: Whether to include CRC32
        """
        
        # Load cover image
        img = Image.open(cover_path)
        
        # Prepare payload
        payload = base64.b64encode(message.encode('utf-8'))
        
        # Build LSB1 header
        flags = 0x01 if use_crc else 0x00  # Bit 0 = HAS_CRC32
        header = self.magic
        header += bytes([self.version])
        header += bytes([flags])
        header += struct.pack('>I', len(payload))
        
        if use_crc:
            crc = zlib.crc32(payload) & 0xFFFFFFFF
            header += struct.pack('>I', crc)
            crc_str = format(crc, '08X')
        else:
            crc_str = None
        
        # Combine header and payload
        full_data = header + payload
        
        # Check capacity
        capacity = self.calculate_capacity(img.width, img.height)
        if len(full_data) > capacity:
            raise ValueError(f"Message too large: {len(full_data)} bytes > {capacity} bytes capacity")
        
        # Embed data
        stego = self.embed_bits(img, full_data)
        
        # Save stego image
        stego.save(str(output_path), 'PNG', optimize=False, compress_level=0)
        
        # Verify by decoding immediately
        verification = self.decode_image(output_path)
        if verification.get('decoded_text') != message:
            raise ValueError("Verification failed - encode/decode mismatch")
        
        return {
            'payload_length': len(payload),
            'total_embedded': len(full_data),
            'capacity_bytes': capacity,
            'crc32': crc_str,
            'verified': True
        }
    
    def decode_image(self, img_path: Path) -> Dict[str, Any]:
        """
        Decode a message from a stego image
        
        Args:
            img_path: Path to stego image
        """
        
        img = Image.open(img_path)
        
        # Extract header first (14 bytes max with CRC)
        header_data = self.extract_bits(img, 14)
        
        # Check for LSB1 magic
        if header_data[:4] != self.magic:
            # Try legacy format
            # Extract more data for legacy detection
            data = self.extract_bits(img, min(1000, self.calculate_capacity(img.width, img.height)))
            
            # Find null terminator
            null_idx = data.find(b'\x00')
            if null_idx > 0:
                payload = data[:null_idx]
                try:
                    decoded = base64.b64decode(payload)
                    text = decoded.decode('utf-8')
                    return {
                        'format': 'legacy',
                        'decoded_text': text,
                        'payload_length': len(payload)
                    }
                except Exception as e:
                    return {'error': f'Legacy decode failed: {e}'}
            
            return {'error': 'No LSB1 header or valid legacy payload found'}
        
        # Parse LSB1 header
        version = header_data[4]
        flags = header_data[5]
        payload_length = struct.unpack('>I', header_data[6:10])[0]
        
        has_crc = bool(flags & 0x01)
        
        if has_crc:
            crc_expected = struct.unpack('>I', header_data[10:14])[0]
            header_size = 14
        else:
            crc_expected = None
            header_size = 10
        
        # Extract full message
        total_bytes = header_size + payload_length
        full_data = self.extract_bits(img, total_bytes)
        
        # Extract payload
        payload = full_data[header_size:header_size + payload_length]
        
        # Verify CRC if present
        if has_crc:
            crc_calculated = zlib.crc32(payload) & 0xFFFFFFFF
            if crc_calculated != crc_expected:
                return {
                    'error': 'CRC32 mismatch',
                    'expected_crc': format(crc_expected, '08X'),
                    'calculated_crc': format(crc_calculated, '08X')
                }
        
        # Decode payload
        try:
            decoded = base64.b64decode(payload)
            text = decoded.decode('utf-8')
            
            result = {
                'magic': 'LSB1',
                'version': version,
                'flags': flags,
                'payload_length': payload_length,
                'decoded_text': text
            }
            
            if has_crc:
                result['crc32'] = format(crc_expected, '08X')
                
            return result
            
        except Exception as e:
            return {'error': f'Decode failed: {e}'}


def cli_encode():
    """CLI for encoding"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Encode message in PNG using LSB steganography')
    parser.add_argument('cover', type=Path, help='Cover image path')
    parser.add_argument('output', type=Path, help='Output stego image path')
    parser.add_argument('--message', '-m', required=True, help='Message to encode')
    parser.add_argument('--no-crc', action='store_true', help='Disable CRC32')
    parser.add_argument('--bpc', type=int, default=1, help='Bits per channel (1 or 4)')
    
    args = parser.parse_args()
    
    codec = LSBCodec(bpc=args.bpc)
    
    try:
        result = codec.encode_message(args.cover, args.message, args.output, use_crc=not args.no_crc)
        print(f"✅ Encoded {result['payload_length']} bytes")
        if result.get('crc32'):
            print(f"CRC32: {result['crc32']}")
        print(f"Capacity used: {result['total_embedded']}/{result['capacity_bytes']} bytes")
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


def cli_decode():
    """CLI for decoding"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Decode message from PNG using LSB steganography')
    parser.add_argument('image', type=Path, help='Stego image path')
    parser.add_argument('--bpc', type=int, default=1, help='Bits per channel (1 or 4)')
    
    args = parser.parse_args()
    
    codec = LSBCodec(bpc=args.bpc)
    
    try:
        result = codec.decode_image(args.image)
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            return 1
        
        print(f"Protocol: {result.get('magic', 'legacy')}")
        print(f"Message: {result['decoded_text']}")
        
        if 'crc32' in result:
            print(f"CRC32: {result['crc32']} ✓")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


def cli_cover():
    """CLI for creating cover images"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Create cover image for LSB steganography')
    parser.add_argument('width', type=int, help='Image width')
    parser.add_argument('height', type=int, help='Image height')
    parser.add_argument('output', type=Path, help='Output image path')
    parser.add_argument('--pattern', default='noise', choices=['noise', 'gradient', 'texture'],
                       help='Pattern type')
    
    args = parser.parse_args()
    
    codec = LSBCodec()
    
    try:
        img = codec.create_cover_image(args.width, args.height, args.pattern)
        img.save(str(args.output), 'PNG')
        
        capacity = codec.calculate_capacity(args.width, args.height)
        print(f"✅ Created {args.width}x{args.height} {args.pattern} cover")
        print(f"Capacity: {capacity:,} bytes")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


def main():
    """Main CLI interface"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='LSB Encoder/Decoder for Echo-Community-Toolkit')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Encode command
    encode_parser = subparsers.add_parser('encode', help='Encode message in image')
    encode_parser.add_argument('cover', type=Path, help='Cover image')
    encode_parser.add_argument('output', type=Path, help='Output stego image')
    encode_parser.add_argument('--message', '-m', required=True, help='Message to encode')
    encode_parser.add_argument('--no-crc', action='store_true', help='Disable CRC32')
    
    # Decode command  
    decode_parser = subparsers.add_parser('decode', help='Decode message from image')
    decode_parser.add_argument('image', type=Path, help='Stego image')
    
    # Cover command
    cover_parser = subparsers.add_parser('cover', help='Create cover image')
    cover_parser.add_argument('width', type=int, help='Width')
    cover_parser.add_argument('height', type=int, help='Height')
    cover_parser.add_argument('output', type=Path, help='Output path')
    cover_parser.add_argument('--pattern', default='noise', 
                             choices=['noise', 'gradient', 'texture'])
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    codec = LSBCodec()
    
    if args.command == 'encode':
        result = codec.encode_message(args.cover, args.message, args.output, 
                                    use_crc=not args.no_crc)
        print(json.dumps(result, indent=2))
        
    elif args.command == 'decode':
        result = codec.decode_image(args.image)
        print(json.dumps(result, indent=2))
        
    elif args.command == 'cover':
        img = codec.create_cover_image(args.width, args.height, args.pattern)
        img.save(str(args.output), 'PNG')
        print(f"Created {args.output}")
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())

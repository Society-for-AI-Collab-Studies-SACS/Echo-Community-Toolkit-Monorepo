#!/usr/bin/env python3
"""
LSB Extractor - Echo-Community-Toolkit
Decoder engine with LSB1 protocol support and legacy fallback
"""

import base64
import json
import struct
import zlib
from pathlib import Path
from typing import Dict, Optional, List, Any
from PIL import Image
import numpy as np


class LSBExtractor:
    """
    LSB Extractor with support for:
    - LSB1 protocol with CRC32 validation
    - Legacy null-terminated format
    - Batch processing
    - Debug mode with raw bit extraction
    """
    
    def __init__(self, include_bits: bool = False):
        self.include_bits = include_bits
        self.magic = b"LSB1"
        
    def extract_bits_from_image(self, img_path: Path) -> bytes:
        """Extract LSB bits from image in MSB-first order"""
        
        img = Image.open(img_path)
        
        # Convert to RGB if needed
        if img.mode not in ['RGB', 'RGBA']:
            raise ValueError(f"Image mode {img.mode} not supported. Use RGB/RGBA PNG.")
            
        pixels = np.array(img)
        height, width = pixels.shape[:2]
        
        # Extract bits in row-major order
        bits = []
        for y in range(height):
            for x in range(width):
                pixel = pixels[y, x]
                # R, G, B channels only (ignore alpha)
                for c in range(3):
                    bits.append(pixel[c] & 1)
        
        # Pack bits into bytes (MSB-first)
        bytes_data = bytearray()
        for i in range(0, len(bits), 8):
            if i + 8 <= len(bits):
                byte = 0
                for j in range(8):
                    byte = (byte << 1) | bits[i + j]  # MSB-first packing
                bytes_data.append(byte)
        
        return bytes(bytes_data)
    
    def parse_lsb1_header(self, data: bytes) -> Optional[Dict]:
        """Parse LSB1 protocol header"""
        
        if len(data) < 10:  # Minimum header size
            return None
            
        # Check magic bytes
        if data[:4] != self.magic:
            return None
        
        try:
            # Parse header
            version = data[4]
            flags = data[5]
            payload_length = struct.unpack('>I', data[6:10])[0]
            
            # Check for CRC32 flag
            has_crc = bool(flags & 0x01)
            
            if has_crc and len(data) < 14:
                return None
            
            header_info = {
                'magic': 'LSB1',
                'version': version,
                'flags': flags,
                'has_crc': has_crc,
                'payload_length': payload_length
            }
            
            if has_crc:
                header_info['crc32'] = struct.unpack('>I', data[10:14])[0]
                header_info['payload_start'] = 14
            else:
                header_info['payload_start'] = 10
            
            # Extract payload
            payload_start = header_info['payload_start']
            payload_end = payload_start + payload_length
            
            if len(data) < payload_end:
                return None
                
            header_info['payload'] = data[payload_start:payload_end]
            
            # Verify CRC if present
            if has_crc:
                calculated_crc = zlib.crc32(header_info['payload']) & 0xFFFFFFFF
                if calculated_crc != header_info['crc32']:
                    header_info['crc_mismatch'] = True
                    header_info['calculated_crc'] = format(calculated_crc, '08X')
                
            return header_info
            
        except Exception:
            return None
    
    def extract_legacy_payload(self, data: bytes) -> bytes:
        """Extract null-terminated Base64 payload (legacy format)"""
        
        # Find null terminator
        null_idx = data.find(b'\x00')
        
        if null_idx > 0:
            return data[:null_idx]
        
        # Try to find valid Base64 content
        valid_chars = b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='
        
        for i, byte in enumerate(data):
            if byte not in valid_chars:
                if i > 0:
                    return data[:i]
                break
        
        return b""
    
    def decode_base64_payload(self, payload: bytes) -> tuple:
        """Decode Base64 payload to UTF-8 text"""
        
        try:
            decoded = base64.b64decode(payload)
            text = decoded.decode('utf-8')
            return text, None
        except Exception as e:
            return None, str(e)
    
    def extract_from_image(self, img_path: Path) -> Dict[str, Any]:
        """Main extraction function with protocol detection"""
        
        result = {
            'filename': img_path.name,
        }
        
        try:
            # Extract raw bits
            data = self.extract_bits_from_image(img_path)
            
            if self.include_bits:
                result['binary_lsb_data'] = base64.b64encode(data).decode('ascii')
            
            # Try LSB1 protocol first
            header = self.parse_lsb1_header(data)
            
            if header:
                # LSB1 format detected
                result.update({
                    'magic': header['magic'],
                    'version': header['version'],
                    'flags': header['flags'],
                    'payload_length': header['payload_length']
                })
                
                if header.get('has_crc'):
                    crc_value = header.get('crc32', 0)
                    result['crc32'] = format(crc_value, '08X')
                    
                    if header.get('crc_mismatch'):
                        result['error'] = 'CRC32 mismatch'
                        result['calculated_crc'] = header['calculated_crc']
                
                # Decode payload
                text, error = self.decode_base64_payload(header['payload'])
                
                if text:
                    result['base64_payload'] = header['payload'].decode('ascii')
                    result['decoded_text'] = text
                    result['message_length_bytes'] = header['payload_length']
                elif error:
                    result['error'] = f'Decode error: {error}'
                    
            else:
                # Try legacy format
                payload = self.extract_legacy_payload(data)
                
                if payload:
                    text, error = self.decode_base64_payload(payload)
                    
                    if text:
                        result['base64_payload'] = payload.decode('ascii')
                        result['decoded_text'] = text
                        result['message_length_bytes'] = len(payload)
                        result['format'] = 'legacy'
                    elif error:
                        result['error'] = f'Decode error: {error}'
                else:
                    result['error'] = 'No valid payload found'
                    
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def extract_batch(self, image_paths: List[Path], output_json: Optional[Path] = None) -> List[Dict]:
        """Extract from multiple images"""
        
        results = []
        
        for path in image_paths:
            if path.exists() and path.suffix.lower() == '.png':
                result = self.extract_from_image(path)
                results.append(result)
        
        if output_json:
            with open(output_json, 'w') as f:
                json.dump(results, f, indent=2)
        
        return results


def main():
    """CLI interface for LSB extraction"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract LSB steganography from PNG images')
    parser.add_argument('images', nargs='+', type=Path, help='PNG image(s) to extract from')
    parser.add_argument('--include-bits', action='store_true', help='Include raw bit data in output')
    parser.add_argument('-o', '--output', type=Path, help='Output JSON file for batch results')
    
    args = parser.parse_args()
    
    extractor = LSBExtractor(include_bits=args.include_bits)
    
    if len(args.images) == 1:
        # Single file
        result = extractor.extract_from_image(args.images[0])
        print(json.dumps(result, indent=2))
    else:
        # Batch processing
        results = extractor.extract_batch(args.images, args.output)
        
        for result in results:
            print(f"\n{result['filename']}:")
            if 'decoded_text' in result:
                print(f"  Message: {result['decoded_text'][:100]}...")
                if 'crc32' in result:
                    print(f"  CRC32: {result['crc32']}")
            elif 'error' in result:
                print(f"  Error: {result['error']}")


if __name__ == '__main__':
    main()

"""
Sacred Gold global.res Unpacker and Repacker Tool
Supports extracting strings from global.res to human-readable JSON/TXT,
and rebuilding global.res binary string tables.
"""

import sys

import os
import struct
import json
import argparse

def unpack_res(res_path, output_json_path):
    """
    Extracts binary strings from global.res into a JSON file.
    """
    print(f"Reading {res_path}...")
    with open(res_path, 'rb') as f:
        data = f.read()

    count = struct.unpack('<I', data[:4])[0]
    print(f"Found {count} entries.")

    entries = []
    for i in range(count):
        str_id, offset, unk, byte_len = struct.unpack('<IIII', data[4 + i * 16 : 20 + i * 16])
        real_offset = offset + 4
        raw_bytes = data[real_offset : real_offset + byte_len]
        text = raw_bytes.decode('utf-16le')
        entries.append({
            'id': str_id,
            'unk': unk,
            'text': text
        })

    os.makedirs(os.path.dirname(os.path.abspath(output_json_path)), exist_ok=True)
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    print(f"Successfully unpacked {len(entries)} strings to {output_json_path}")

def pack_res(json_path, output_res_path):
    """
    Compiles JSON strings into a binary global.res resource file.
    """
    print(f"Reading {json_path}...")

    with open(json_path, 'r', encoding='utf-8') as f:
        entries = json.load(f)

    print(f"Packing {len(entries)} strings into {output_res_path}...")
    header = struct.pack('<I', len(entries))
    index_records = []
    strings_data = bytearray()

    current_real_offset = 4 + len(entries) * 16

    for e in entries:
        raw_str = e['text'].encode('utf-16le')
        byte_len = len(raw_str)
        stored_offset = current_real_offset - 4
        unk = e.get('unk', 0)
        index_records.append(struct.pack('<IIII', e['id'], stored_offset, unk, byte_len))
        strings_data.extend(raw_str)
        current_real_offset += byte_len

    repacked_data = header + b''.join(index_records) + strings_data

    os.makedirs(os.path.dirname(os.path.abspath(output_res_path)), exist_ok=True)
    with open(output_res_path, 'wb') as f:
        f.write(repacked_data)

    print(f"Successfully created {output_res_path} ({len(repacked_data)} bytes)")

def main():
    """
    CLI entry point for global.res pack and unpack operations.
    """
    parser = argparse.ArgumentParser(description="Sacred Gold global.res pack/unpack tool")

    subparsers = parser.add_subparsers(dest="command", required=True)

    unpack_parser = subparsers.add_parser("unpack", help="Unpack global.res to JSON")
    unpack_parser.add_argument("input", help="Path to input global.res")
    unpack_parser.add_argument("output", help="Path to output JSON file")

    pack_parser = subparsers.add_parser("pack", help="Pack JSON to global.res")
    pack_parser.add_argument("input", help="Path to input JSON file")
    pack_parser.add_argument("output", help="Path to output global.res")

    args = parser.parse_args()

    if args.command == "unpack":
        unpack_res(args.input, args.output)
    elif args.command == "pack":
        pack_res(args.input, args.output)

if __name__ == "__main__":
    main()

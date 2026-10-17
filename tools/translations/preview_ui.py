#!/usr/bin/env python3
"""Render local ROM interface resources for visual QA; output must stay ignored.

These are resource previews, not screenshots from a running game. Palettes are
shown in grayscale to make glyph shape, spacing and tile selection easy to see.
Requires Pillow; never ships or commits the generated images.
"""
import argparse
import struct
from pathlib import Path
from PIL import Image, ImageDraw
from build_ptbr_patch import read_rom
from map_ui import lorom, decompress, map_roms, stripe_size


def sprite(rom, i):
    a=rom[0x51b1+i] | rom[0x50d2+i]<<8 | rom[0x4ff3+i]<<16
    p=lorom(a)
    return rom[p:p+1536] if i<12 else decompress(rom,p)[0]


def tile(image, atlas, value, x, y):
    i=value & 1023
    data=atlas[i*16:i*16+16]
    if len(data)!=16: return
    colors=[(12,17,25),(92,110,130),(180,190,200),(255,255,255)]
    for cy in range(8):
        for cx in range(8):
            c=(data[cy*2]>>(7-cx)&1) | (data[cy*2+1]>>(7-cx)&1)<<1
            image.putpixel((x+(7-cx if value&0x4000 else cx),y+(7-cy if value&0x8000 else cy)),colors[c])


def rectangle(atlas, data, width):
    values=struct.unpack('<'+str(len(data)//2)+'H',data)
    out=Image.new('RGB',(width*8,(len(values)//width)*8),(12,17,25))
    for i,v in enumerate(values): tile(out,atlas,v,(i%width)*8,(i//width)*8)
    return out


def menu(rom, offset):
    data=rom[offset:offset+stripe_size(rom,offset)]
    atlas=rom[0x70000:0x71000]+sprite(rom,0x6b)[:1536]
    words={};p=0
    while data[p]<128:
        dst=int.from_bytes(data[p:p+2],'big')
        flags=data[p+2];n=(int.from_bytes(data[p+2:p+4],'big')&0x3fff)+1
        p+=4
        for j in range((n+1)//2):
            pos=p if flags&64 else p+j*2
            words[dst+j*(32 if flags&128 else 1)]=int.from_bytes(data[pos:pos+2],'little')
        p+=2 if flags&64 else n
    out=Image.new('RGB',(256,256),(12,17,25))
    base=0x6000
    for addr,v in words.items():
        if base<=addr<base+0x400:
            pos=addr-base;tile(out,atlas,v,(pos%32)*8,(pos//32)*8)
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--us-rom',required=True);p.add_argument('--translated-rom',required=True)
    p.add_argument('--output',default='build/ptbr-ui-preview.png');args=p.parse_args()
    us,pt=read_rom(args.us_rom),read_rom(args.translated_rom)
    m=map_roms(us,pt)
    table=next(e for e in m['entries'] if e['name']=='kHudItemText')
    image=Image.new('RGB',(1080,960),(28,32,42));draw=ImageDraw.Draw(image)
    draw.text((20,12),'LOCAL RESOURCE PREVIEW - US / PT-BR (grayscale)',fill='white')
    for column,rom in enumerate((us,pt)):
        x=20+column*540
        draw.text((x,38),'US' if column==0 else 'PT-BR',fill='white')
        atlas=sprite(rom,0x6a)+sprite(rom,0x6b)+sprite(rom,0x69)
        for i in range(20):
            data=rom[table['offset']+i*32:table['offset']+i*32+32]
            item=rectangle(atlas,data,8).resize((128,32),Image.Resampling.NEAREST)
            xx=x+(i%3)*170;yy=66+(i//3)*48
            image.paste(item,(xx,yy));draw.text((xx,yy+32),str(i+1),fill='white')
        out=menu(rom,lorom(0xce2a8))
        image.paste(out.resize((512,512),Image.Resampling.NEAREST),(x,430))
    image.save(args.output)
    names=Image.new('RGB',(1080,600),(28,32,42))
    for col,rom in enumerate((us,pt)):
        names.paste(menu(rom,lorom(0xce7bf)).resize((512,512),Image.Resampling.NEAREST),(20+540*col,40))
    names.save(str(Path(args.output).with_name('ptbr-ui-name-preview.png')))
    print(args.output)


if __name__=='__main__': main()

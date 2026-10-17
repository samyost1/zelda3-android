"""Render production second-screen atlases with real US assets and PT-BR UI active.

Run verify_ptbr.py with your ROMs first; both binary fixtures stay in ignored build/.
"""
import os
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path
from test_gamepad_native import ROOT, SRC, toolchain
from test_save_native import function


class SecondScreenNativeTests(unittest.TestCase):
    def test_atlases_stay_original_across_language_activation_and_cache(self):
        tc = toolchain()
        base = ROOT / 'build/ui-second-screen-base.bin'
        package = ROOT / 'build/ui-package.bin'
        if os.name != 'nt' or not tc or not base.exists() or not package.exists():
            self.skipTest('Requires NDK and real-ROM fixtures from verify_ptbr.py')
        fixture = base.read_bytes()
        arrays = 'static uint16 palette[]={' + ','.join(map(str, struct.unpack('<64H', fixture[:128]))) + '};\n'
        at = 128
        for index in (0x6a, 0x6b, 0x69):
            size, = struct.unpack_from('<I', fixture, at)
            at += 4
            arrays += f'static uint8 bank_{index:x}[]={{' + ','.join(map(str, fixture[at:at+size])) + '};\n'
            at += size
        self.assertEqual(at, len(fixture))
        arrays += 'static uint8 package[]={' + ','.join(map(str, package.read_bytes())) + '};\n'
        prefix = r'''
typedef unsigned char uint8;
typedef unsigned short uint16;
typedef unsigned int uint32;
typedef unsigned long long size_t;
typedef _Bool bool;
#define true 1
#define false 0
#define NULL ((void*)0)
#define countof(x) (sizeof(x)/sizeof((x)[0]))
typedef struct {const uint8 *ptr; size_t size;} MemBlk;
void *memcpy(void*d,const void*s,size_t n) {uint8*x=d;const uint8*y=s;while(n--)*x++=*y++;return d;}
void *memset(void*d,int c,size_t n) {uint8*x=d;while(n--)*x++=c;return d;}
int memcmp(const void*a,const void*b,size_t n) {const uint8*x=a,*y=b;while(n--){if(*x!=*y)return *x-*y;x++;y++;}return 0;}
int strcmp(const char*a,const char*b) {while(*a&&*a==*b){a++;b++;}return *a-*b;}
#define CHECK(x) if (!(x)) return __LINE__;
static uint8 g_ss_tiles[384*64];
static bool g_ss_tiles_ready;
static int decoded;
MemBlk FindInAssetArray(int asset,int index);
#define kSprGfx(i) UiTranslation_Block(0x100+(i),FindInAssetArray(64,i))
#define kHudPalData palette
'''
        metadata = (SRC/'ui_translation_data.h').read_text().replace('#pragma once', '')
        header = '\n'.join(x for x in (SRC/'ui_translation.h').read_text().splitlines() if not x.startswith('#'))
        loader = '\n'.join(x for x in (SRC/'ui_translation.c').read_text().splitlines() if not x.startswith('#include'))
        decoder = function((SRC/'load_gfx.c').read_text(), 'int Decompress(').replace('{', '{ decoded++;', 1)
        funcs = 'static bool SS_AssetsReady(void) {return true;}\n'
        screen = (SRC/'second_screen.c').read_text()
        for signature in ['static void SS_EnsureTiles(', 'static uint32 SS_Snes555(',
                          'static uint32 SS_HudColor(', 'static void SS_DrawTile(',
                          'static void SS_StripBg(', 'bool SS_RenderIconSheet(',
                          'bool SS_RenderGlyphSheet(', 'bool SS_RenderLetterSheet(']:
            funcs += function(screen, signature)
        assets = r'''
MemBlk FindInAssetArray(int asset,int index) {
 if(asset==64) switch(index) {
  case 0x6a: return (MemBlk){bank_6a,sizeof(bank_6a)};
  case 0x6b: return (MemBlk){bank_6b,sizeof(bank_6b)};
  case 0x69: return (MemBlk){bank_69,sizeof(bank_69)};
 }
 return (MemBlk){NULL,0};
}
static uint32 original_icons[160*128],original_glyphs[96*32],original_letters[128*16];
static uint32 icons[160*128],glyphs[96*32],letters[128*16];
int check_atlases(void) {
 CHECK(SS_RenderLetterSheet(letters)); CHECK(!memcmp(letters,original_letters,sizeof(letters)));
 CHECK(SS_RenderGlyphSheet(glyphs)); CHECK(!memcmp(glyphs,original_glyphs,sizeof(glyphs)));
 CHECK(SS_RenderIconSheet(icons)); CHECK(!memcmp(icons,original_icons,sizeof(icons)));
 return 0;
}
int tests(void) {
 CHECK(SS_RenderIconSheet(original_icons));
 CHECK(SS_RenderGlyphSheet(original_glyphs));
 CHECK(SS_RenderLetterSheet(original_letters)); CHECK(decoded==3);
 CHECK(UiTranslation_Select("pt-br",(MemBlk){package,sizeof(package)}));
 CHECK(UiTranslation_Active());
 // The game must still receive the translated bank; only SS bypasses it.
 CHECK(kSprGfx(0x69).ptr!=bank_69);
 int result=check_atlases();if(result)return result;CHECK(decoded==3);
 // Reproduce first opening of the second screen AFTER PT-BR activation.
 g_ss_tiles_ready=false;
 result=check_atlases();if(result)return result;CHECK(decoded==6);
 UiTranslation_Defer();result=check_atlases();if(result)return result;CHECK(decoded==6);
 CHECK(UiTranslation_Resume());result=check_atlases();if(result)return result;CHECK(decoded==6);
 CHECK(!UiTranslation_Select("us",(MemBlk){NULL,0}));
 result=check_atlases();if(result)return result;CHECK(decoded==6);
 g_ss_tiles_ready=false;
 result=check_atlases();if(result)return result;CHECK(decoded==9);
 return 0;
}
'''
        source = (prefix + metadata + header + loader + arrays +
                  (SRC/'second_screen_tables.h').read_text() + decoder + funcs + assets)
        with tempfile.TemporaryDirectory(prefix='zelda-ss-native-') as directory:
            path = Path(directory)
            (path/'test.c').write_text(source)
            subprocess.run([str(tc/'clang.exe'), '--target=x86_64-pc-windows-msvc', '-O1',
                            '-ffreestanding', '-fno-stack-protector', '-mno-stack-arg-probe', '-c', str(path/'test.c'),
                            '-o', str(path/'test.obj')], check=True)
            subprocess.run([str(tc/'ld.lld.exe'), '-flavor', 'link', '/entry:tests', '/subsystem:console',
                            '/nodefaultlib', '/stack:1048576,1048576', str(path/'test.obj'),
                            '/out:'+str(path/'test.exe')], check=True)
            result = subprocess.run([str(path/'test.exe')])
            if result.returncode:
                (ROOT/'build/second-screen-failed.c').write_text(source)
            self.assertEqual(result.returncode, 0, 'second-screen assertion at C line '+str(result.returncode))

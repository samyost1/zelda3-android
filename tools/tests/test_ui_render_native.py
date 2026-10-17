"""Exercise production credits and game-over renderers against ROM resources."""
from pathlib import Path
import os
import struct
import subprocess
import tempfile
import unittest
import sys
from test_gamepad_native import toolchain, ROOT, SRC
from test_save_native import function
sys.path.insert(0,str(ROOT/'tools/translations'))
from map_ui import decompress


class NativeUiRenderTests(unittest.TestCase):
    def test_credits_captions_names_and_gameover(self):
        tc = toolchain()
        p = ROOT / 'build/ui-package.bin'
        if os.name != 'nt' or not tc or not p.exists():
            self.skipTest('Requires NDK and package from verify_ptbr.py')
        package = p.read_bytes()
        entries = {}
        for i in range(struct.unpack_from('<I', package, 12)[0]):
            id, off, n = struct.unpack_from('<III', package, 40+i*12)
            entries[id] = package[off:off+n]
        captions, offsets = entries[0x403], struct.unpack('<17H', entries[0x404])
        expected = []
        sizes = []
        gfx_expected = []
        gfx_checks = []
        for id, data in entries.items():
            if not 0x100 <= id < 0x300: continue
            raw = id < 0x10c
            dec = data if raw else decompress(data,0)[0]
            at = len(gfx_expected); gfx_expected.extend(dec)
            gfx_checks.append((id,at,len(dec),raw))
        for start, end in zip(offsets, offsets[1:]):
            words = [0x60, 0xfe47, 0x3ca9]
            while start < end:
                words.extend(struct.unpack_from('<2H', captions, start))
                n = int.from_bytes(captions[start+2:start+4], 'big')+1
                start += 4
                color = captions[start] << 8
                words.extend(color | c for c in captions[start+1:start+1+n//2])
                start += 1+n//2
            self.assertEqual(start, end)
            sizes.append(len(words))
            expected.extend(words)
        prefix = r'''
typedef unsigned char uint8;
typedef signed char int8;
typedef unsigned short uint16;
typedef unsigned int uint32;
typedef unsigned long long size_t;
typedef _Bool bool;
#define true 1
#define false 0
#define NULL ((void*)0)
#define countof(x) (sizeof(x)/sizeof((x)[0]))
#define WORD(x) (*(uint16*)&(x))
#define BYTE(x) (*(uint8*)&(x))
typedef struct { const uint8 *ptr; size_t size; } MemBlk;
int memcmp(const void *a,const void*b,size_t n) {const uint8*x=a,*y=b;while(n--){if(*x!=*y)return *x-*y;x++;y++;}return 0;}
int strcmp(const char*a,const char*b) {while(*a&&*a==*b){a++;b++;}return *a-*b;}
void *memcpy(void*d,const void*s,size_t n) {uint8*x=d;const uint8*y=s;while(n--)*x++=*y++;return d;}
MemBlk FindInAssetArray(int asset,int index) {static const uint8 empty[]={255};return (MemBlk){empty,1};}
#define kSprGfx(i) UiTranslation_Block(0x100+(i),FindInAssetArray(64,i))
#define kBgGfx(i) UiTranslation_Block(0x200+(i),FindInAssetArray(65,i))
int Decompress(uint8*,const uint8*);
static uint16 swap16(uint16 v) {return (v<<8)|(v>>8);}
#define CHECK(x) if (!(x)) return __LINE__;
uint16 vram_upload_data[4096],vram_upload_offset,R16,R18,ending_which_dung,deaths_per_palace[16];
uint8 g_ram[131072],nmi_load_bg_from_vram,submodule_index;
uint16 kEnding_MapData[160];
uint8 kEnding_Credits_Text[4096]={255},kEnding0_Data[2048]={0x62,0x68,0,1,0};
uint16 kEnding_Credits_Offs[394],kEnding0_Offs[17]={0,5};
uint8 flag_for_boomerang_in_place,hookshot_effect_index,cur_object_index,sound_effect_2;
uint8 ancilla_x_lo[10],ancilla_x_hi[10],ancilla_x_vel[10],ancilla_type[10];
void Ancilla_MoveX(int k) {ancilla_x_lo[k]+=(int8)ancilla_x_vel[k]/16;}
uint16 Ancilla_GetX(int k) {return ancilla_x_lo[k]|ancilla_x_hi[k]<<8;}
typedef struct {uint8 x,y,ch,flags;} OamEnt;
OamEnt oam_storage[32];
uint16 oam_cur_ptr,oam_ext_cur_ptr;
int oam_count;
OamEnt *GetOamCurPtr(void) {oam_count=0;return oam_storage;}
void Ancilla_SetOam(OamEnt *o,int x,int y,int ch,int flags,int size) {o->x=x;o->y=y;o->ch=ch;o->flags=flags;oam_count++;}
void GameOverText_Draw(void);
'''
        metadata = (SRC/'ui_translation_data.h').read_text().replace('#pragma once','')
        header = '\n'.join(x for x in (SRC/'ui_translation.h').read_text().splitlines() if not x.startswith('#'))
        loader = '\n'.join(x for x in (SRC/'ui_translation.c').read_text().splitlines() if not x.startswith('#include'))
        funcs = ''
        for file, names in [('ending.c',['Credits_AddNextAttribution','Credits_AddEndingSequenceText']),
                            ('ancilla.c',['GameOverText_Draw']),
                            ('messaging.c',['Death_InitializeGameOverLetters','GameOverText_SweepLeft','GameOverText_UnfurlRight'])]:
            text=(SRC/file).read_text()
            for name in names: funcs+=function(text,'void '+name+'(')+'\n'
        gfx=(SRC/'load_gfx.c').read_text()
        for signature in ['static const uint8 *GetCompSpritePtr(', 'int Decomp_spr(', 'int Decomp_bg(', 'int Decompress(']:
            funcs+=function(gfx,signature)+'\n'
        arrays = 'static uint8 package[]={' + ','.join(map(str,package)) + '};\n'
        arrays += 'static uint16 expected[]={' + ','.join(map(str,expected)) + '};\n'
        arrays += 'static int sizes[]={' + ','.join(map(str,sizes)) + '};\n'
        arrays += 'static uint8 gfx_expected[]={' + ','.join(map(str,gfx_expected)) + '};\n'
        graphics_test = 'static uint8 buffer[4098];\n'
        for id,at,n,raw in gfx_checks:
            if raw:
                graphics_test+=f'CHECK(!memcmp(GetCompSpritePtr({id-0x100}),gfx_expected+{at},{n}));\n'
            else:
                call=f'Decomp_spr(buffer+1,{id-0x100})' if id<0x200 else f'Decomp_bg(buffer+1,{id-0x200})'
                graphics_test+=f'buffer[0]=0xaa;buffer[{n+1}]=0xbb; CHECK({call}=={n}); CHECK(!memcmp(buffer+1,gfx_expected+{at},{n})); CHECK(buffer[0]==0xaa && buffer[{n+1}]==0xbb);\n'
        test = r'''
int tests(void) {
 CHECK(UiTranslation_Select("pt-br",(MemBlk){package,sizeof(package)}));
 GRAPHICS_TEST
 int pos=0;
 for(int i=0;i<16;i++) {
   submodule_index=i*2; Credits_AddEndingSequenceText();
   CHECK(vram_upload_offset==sizes[i]*2);
   for(int j=0;j<sizes[i];j++) CHECK(vram_upload_data[j]==expected[pos++]);
 }
 const uint8 *rows=UiTranslation_Get(kUi_CreditsText,NULL);
 const uint16 *off=UiTranslation_Get(kUi_CreditsOffsets,NULL);
 for(int i=0;i<394;i++) {
   R18=i;R16=0x6800;ending_which_dung=0;vram_upload_offset=0;Credits_AddNextAttribution();
   CHECK(vram_upload_data[2]==0x3ca9);
   const uint8 *row=rows+off[i];
   if(row[0]!=255) for(int j=0;j<(row[1]+1)/2;j++)
     CHECK(vram_upload_data[5+j]==(row[2]<<8|row[3+j]));
 }
 Death_InitializeGameOverLetters();
 CHECK(ancilla_x_lo[8]==0xb0 && ancilla_x_hi[8]==0);
 int steps=0;
 while(ancilla_type[0]==1 && steps++<512) GameOverText_SweepLeft();
 CHECK(steps<512 && flag_for_boomerang_in_place==8);
 while(ancilla_type[0]==2 && steps++<1024) GameOverText_UnfurlRight();
 CHECK(steps<1024 && ancilla_type[0]==3);
 const uint8 *target=UiTranslation_Get(kUi_GameOverUnfurl,NULL);
 const uint16 *letters=UiTranslation_Get(kUi_GameOverCharacters,NULL);
 GameOverText_Draw(); CHECK(oam_count==18);
 for(int i=0;i<9;i++) CHECK(ancilla_x_lo[i]==target[i]);
 // Draw order is last letter first; attributes include the mirrored tile.
 for(int i=0;i<9;i++) for(int j=0;j<2;j++) {
   OamEnt *o=&oam_storage[(8-i)*2+j];
   CHECK(o->ch==(uint8)letters[i*2+j] && o->flags==letters[i*2+j]>>8);
 }
 UiTranslation_Select("us",(MemBlk){NULL,0});
 Death_InitializeGameOverLetters();steps=0;
 while(ancilla_type[0]==1 && steps++<512) GameOverText_SweepLeft();
 while(ancilla_type[0]==2 && steps++<1024) GameOverText_UnfurlRight();
 CHECK(steps<1024 && flag_for_boomerang_in_place==7 && ancilla_type[0]==3);
 GameOverText_Draw(); CHECK(oam_count==16);
 // A pre-update snapshot can resume the eight-letter animation after the
 // importer has activated PT-BR. In particular, the last unfurl step must
 // not walk backwards beyond the ancilla arrays when the count grows.
 Death_InitializeGameOverLetters();steps=0;
 while(ancilla_type[0]==1 && steps++<512) GameOverText_SweepLeft();
 while(hookshot_effect_index<7 && steps++<1024) GameOverText_UnfurlRight();
 CHECK(steps<1024 && ancilla_type[0]==2);
 CHECK(UiTranslation_Select("pt-br",(MemBlk){package,sizeof(package)}));
 while(ancilla_type[0]==2 && steps++<2048) GameOverText_UnfurlRight();
 CHECK(steps<2048 && ancilla_type[0]==3 && flag_for_boomerang_in_place==8);
 GameOverText_Draw(); CHECK(oam_count==18);
 // Loading the larger animation in the original language is bounded too.
 UiTranslation_Select("us",(MemBlk){NULL,0});
 ancilla_type[0]=2;hookshot_effect_index=0;steps=0;
 while(ancilla_type[0]==2 && steps++<512) GameOverText_UnfurlRight();
 CHECK(steps<512 && ancilla_type[0]==3 && flag_for_boomerang_in_place==7);
 GameOverText_Draw();CHECK(oam_count==16);
 return 0;
}
'''.replace('GRAPHICS_TEST',graphics_test)
        with tempfile.TemporaryDirectory(prefix='zelda-ui-render-') as temp:
            path=Path(temp); source=prefix+metadata+header+loader+funcs+arrays+test
            (path/'test.c').write_text(source)
            subprocess.run([str(tc/'clang.exe'),'--target=x86_64-pc-windows-msvc','-O1',
                            '-ffreestanding','-fno-stack-protector','-c',str(path/'test.c'),
                            '-o',str(path/'test.obj')],check=True)
            subprocess.run([str(tc/'ld.lld.exe'),'-flavor','link','/entry:tests','/subsystem:console',
                            '/nodefaultlib',str(path/'test.obj'),'/out:'+str(path/'test.exe')],check=True)
            result=subprocess.run([str(path/'test.exe')])
            if result.returncode: (ROOT/'build/ui-render-failed.c').write_text(source)
            self.assertEqual(result.returncode,0,'native UI render assertion at C line '+str(result.returncode))

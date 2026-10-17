"""Run the actual snapshot UI restoration paths, including animated menus."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest
from test_gamepad_native import toolchain, ROOT, SRC


class UiRestoreTests(unittest.TestCase):
    def test_opening_inventory_and_deferred_old_screens(self):
        tc=toolchain()
        if os.name!='nt' or not tc:
            self.skipTest('Requires Windows NDK')
        source='\n'.join(s for s in (SRC/'ui_translation_state.c').read_text().splitlines()
                         if not s.startswith('#include'))
        prefix=r'''
typedef unsigned char uint8;
typedef unsigned short uint16;
typedef unsigned int uint32;
typedef unsigned long long size_t;
typedef _Bool bool;
#define true 1
#define false 0
#define NULL ((void*)0)
typedef struct {const uint8 *ptr;size_t size;} MemBlk;
uint8 g_ram[131072],old_font[4096],new_font[4096];
uint8 old_sprite[1536],new_sprite[1536],ancilla_type[10],ancilla_x_lo[10],ancilla_x_hi[10];
uint8 flag_for_boomerang_in_place;
const uint8 target[9]={0x50,0x58,0x60,0x70,0x78,0x88,0x90,0x98,0xa0};
uint16 vram[32768];
struct {uint16 *vram;} g_zenv={vram};
int main_module_index,submodule_index,overworld_map_state;
bool active=true,deferred;
int draws;
enum {kUi_InterfaceFont=1024,kUi_sprite_05=261,kUi_GameOverUnfurl=0x408};
void *memcpy(void*d,const void*s,size_t n) {uint8*x=d;const uint8*y=s;while(n--)*x++=*y++;return d;}
int memcmp(const void*a,const void*b,size_t n) {const uint8*x=a,*y=b;while(n--){if(*x!=*y)return*x-*y;x++;y++;}return 0;}
bool UiTranslation_Active(void) {return active&&!deferred;}
void UiTranslation_Defer(void) {deferred=true;}
bool UiTranslation_Resume(void) {bool was=deferred;deferred=false;return was;}
bool UiTranslation_OriginalTiles(const uint8*data,const uint8*old,const uint8*pt,size_t n) {return !memcmp(data,old,n)&&memcmp(old,pt,n);}
bool UiTranslation_RestoreTiles(uint8*data,const uint8*old,const uint8*pt,size_t n) {if(!memcmp(data,old,n)){memcpy(data,pt,n);return true;}return false;}
const void *UiTranslation_Get(uint32 id,const void*orig) {return id==kUi_InterfaceFont?new_font:id==kUi_sprite_05?new_sprite:id==kUi_GameOverUnfurl?target:orig;}
MemBlk FindInAssetArray(int a,int b) {return b==5?(MemBlk){old_sprite,1536}:(MemBlk){old_font,2048};}
MemBlk FindIndexInMemblk(MemBlk b,int i) {return (MemBlk){old_font,4096};}
#define kDialogueFont(i) ((MemBlk){old_font,4096})
int Decompress(uint8*d,const uint8*s) {memcpy(d,old_font,2048);return 2048;}
int Decomp_spr(uint8*d,int i) {memcpy(d,new_font,2048);return 2048;}
void Hud_DrawYButtonItems(void) {draws++;g_ram[0x1000]=0x7c;}
void Hud_DrawAbilityBox(void) {draws++;}
void Hud_DrawEquipmentBox(void) {draws++;}
void Hud_DrawSelectedYButtonItem(void) {draws++;}
#define CHECK(x) if(!(x))return __LINE__;
'''
        body=r'''
int tests(void) {
 for(int i=0;i<4096;i++){old_font[i]=0x11;new_font[i]=0x22;}
 main_module_index=14;submodule_index=1;overworld_map_state=2;g_ram[0]=0x91;
 memcpy((uint8*)&vram[0x7000],old_font,2048);
 UiTranslation_RestoreAfterLoad();
 CHECK(draws==4 && ((uint8*)&vram[0x6800])[0]==0x7c);
 CHECK(g_ram[0]==0x91 && UiTranslation_Active());
 // Expanded bottles must keep the old graphics and labels together until
 // a new inventory initialization can redraw the complete surface.
 draws=0;overworld_map_state=8;memcpy((uint8*)&vram[0x7000],old_font,2048);
 UiTranslation_RestoreAfterLoad();
 CHECK(draws==0 && deferred && ((uint8*)&vram[0x7000])[0]==0x11);
 CHECK(g_ram[0]==0x91);
 // A new PT snapshot restores full activation even after an old deferred one.
 memcpy((uint8*)&vram[0x7000],new_font,2048);
 UiTranslation_RestoreAfterLoad();CHECK(UiTranslation_Active() && draws==0);
 main_module_index=1;memcpy((uint8*)&vram[0x7000],old_font,4096);
 UiTranslation_RestoreAfterLoad();CHECK(deferred && ((uint8*)&vram[0x7000])[0]==0x11);
 for(int i=0;i<1536;i++){old_sprite[i]=0x11;new_sprite[i]=0x22;}
 main_module_index=18;submodule_index=7;ancilla_type[0]=3;flag_for_boomerang_in_place=7;
 memcpy((uint8*)&vram[0x4400],old_font,1024);
 UiTranslation_RestoreAfterLoad();
 CHECK(UiTranslation_Active() && flag_for_boomerang_in_place==8);
 CHECK(((uint8*)&vram[0x4400])[0]==0x22);
 for(int i=0;i<9;i++)CHECK(ancilla_x_lo[i]==target[i] && ancilla_x_hi[i]==0);
 CHECK(g_ram[0]==0x91);
 memcpy((uint8*)&vram[0x7000],new_font,4096);
 UiTranslation_RestoreAfterLoad();CHECK(UiTranslation_Active());
 main_module_index=26;memcpy((uint8*)&vram[0x7000],old_font,4096);
 UiTranslation_RestoreAfterLoad();CHECK(deferred && ((uint8*)&vram[0x7000])[0]==0x11);
 return 0;
}
'''
        with tempfile.TemporaryDirectory(prefix='zelda-ui-restore-') as temp:
            d=Path(temp);(d/'test.c').write_text(prefix+source+body)
            subprocess.run([str(tc/'clang.exe'),'--target=x86_64-pc-windows-msvc','-O1',
                            '-ffreestanding','-fno-stack-protector','-c',str(d/'test.c'),'-o',str(d/'test.obj')],check=True)
            subprocess.run([str(tc/'ld.lld.exe'),'-flavor','link','/entry:tests','/subsystem:console',
                            '/nodefaultlib',str(d/'test.obj'),'/out:'+str(d/'test.exe')],check=True)
            result=subprocess.run([str(d/'test.exe')])
            if result.returncode:(ROOT/'build/ui-restore-failed.c').write_text(prefix+source+body)
            self.assertEqual(result.returncode,0,'snapshot restore C line '+str(result.returncode))

"""Run the actual interface package loader with the locally verified package.

First run tools/translations/verify_ptbr.py with your own ROMs. Its ignored
build/ui-package.bin is never a repository fixture or distributed asset.
"""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest
from test_gamepad_native import toolchain, ROOT, SRC


class NativeUiTests(unittest.TestCase):
    def test_package_activation_corruption_and_fallback(self):
        tc = toolchain()
        package = ROOT / 'build/ui-package.bin'
        if os.name != 'nt' or not tc or not package.exists():
            self.skipTest('Requires NDK and the ignored package from verify_ptbr.py')
        self.assertTrue((SRC / 'ui_translation.c').exists(), 'native UI package loader is implemented')
        source = '\n'.join(x for x in (SRC / 'ui_translation.c').read_text().splitlines()
                           if not x.startswith('#include'))
        declarations = '\n'.join(x for x in (SRC / 'ui_translation.h').read_text().splitlines()
                                 if not x.startswith('#include') and not x.startswith('#pragma'))
        metadata = (SRC / 'ui_translation_data.h').read_text().replace('#pragma once', '')
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
typedef struct { const uint8 *ptr; size_t size; } MemBlk;
int memcmp(const void *a, const void *b, size_t n) {
 const uint8 *x=a,*y=b; while(n--) { if(*x!=*y)return *x-*y; x++;y++; } return 0;
}
int strcmp(const char *a,const char*b) { while(*a && *a==*b) {a++;b++;}return *a-*b; }
#define CHECK(x) if (!(x)) return __LINE__;
'''
        body = r'''
int tests(void) {
 uint8 original[2]={3,9}; MemBlk mb={original,2};
 CHECK(!UiTranslation_Select(NULL,(MemBlk){NULL,0}));
 CHECK(!UiTranslation_Active());
 CHECK(UiTranslation_Get(1,original)==original);
 CHECK(!UiTranslation_Select("us",(MemBlk){package,sizeof(package)}));
 CHECK(UiTranslation_Select("pt-br",(MemBlk){package,sizeof(package)}));
 CHECK(UiTranslation_Active());
 CHECK(UiTranslation_Get(kUi_HudItemText,original)!=original);
 CHECK(UiTranslation_Get(99999,original)==original);
 CHECK(UiTranslation_Block(kUi_InterfaceFont,mb).size==4096);
 CHECK(((size_t)UiTranslation_Get(kUi_InterfaceFont,NULL)&3)==0);
 CHECK(UiTranslation_Block(99999,mb).ptr==original);
 static uint8 old_tiles[2048],new_tiles[2048],loaded_tiles[2048];
 for(int i=0;i<2048;i++) old_tiles[i]=loaded_tiles[i]=(uint8)(i*7);
 for(int i=0;i<2048;i++) new_tiles[i]=(uint8)(old_tiles[i]+1);
 // A customized controller glyph survives a restored old inventory state.
 loaded_tiles[0]^=7;
 CHECK(UiTranslation_OriginalTiles(loaded_tiles,old_tiles,new_tiles,2048));
 CHECK(!UiTranslation_OriginalTiles(new_tiles,old_tiles,new_tiles,2048));
 CHECK(UiTranslation_RestoreTiles(loaded_tiles,old_tiles,new_tiles,2048));
 CHECK(loaded_tiles[0]==7 && loaded_tiles[16]==new_tiles[16]);
 // A different graphics bank must not be interpreted as an old UI bank.
 for(int i=0;i<2048;i++) loaded_tiles[i]=77;
 CHECK(!UiTranslation_RestoreTiles(loaded_tiles,old_tiles,new_tiles,2048));
 CHECK(loaded_tiles[16]==77);
 CHECK(!UiTranslation_OriginalTiles(loaded_tiles,old_tiles,new_tiles,2048));
 UiTranslation_Defer();
 CHECK(!UiTranslation_Active() && UiTranslation_Get(1,original)==original);
 CHECK(UiTranslation_NameTile(0x42,false)==0x42);
 CHECK(UiTranslation_Resume() && UiTranslation_Active());
 CHECK(!UiTranslation_Resume());
 const uint8 *map=UiTranslation_Get(kUi_NameFontMap,NULL);
 const uint16 names[][2]={{0,0},{0x28,0x18},{0x42,0x22},{0xa9,0x59},{0xe6,0x34}};
 for (int i=0;i<5;i++) {
   CHECK(UiTranslation_NameTile(names[i][0],false)==map[names[i][1]*3]);
   CHECK(UiTranslation_NameTile(names[i][0],true)==map[names[i][1]*3+1]);
 }
 for (int i=0;i<(int)sizeof(package);i+=97) {
   package[i]^=1;
   CHECK(!UiTranslation_Select("pt-br",(MemBlk){package,sizeof(package)}));
   CHECK(!UiTranslation_Active()); CHECK(UiTranslation_Get(1,original)==original);
   package[i]^=1;
 }
 CHECK(!UiTranslation_Select("pt-br",(MemBlk){package,sizeof(package)-1}));
 CHECK(UiTranslation_Select("pt-br",(MemBlk){package,sizeof(package)}));
 CHECK(!UiTranslation_Select("mod",(MemBlk){package,sizeof(package)}));
 CHECK(!UiTranslation_Active());
 CHECK(UiTranslation_NameTile(0x42,false)==0x42);
 CHECK(UiTranslation_NameTile(0x42,true)==0x52);
 CHECK(!UiTranslation_Resume());
 return 0;
}
'''
        data = 'static uint8 package[]={' + ','.join(str(b) for b in package.read_bytes()) + '};\n'
        with tempfile.TemporaryDirectory(prefix='zelda-ui-native-') as temp:
            path = Path(temp)
            (path/'test.c').write_text(prefix+metadata+declarations+source+data+body)
            subprocess.run([str(tc/'clang.exe'),'--target=x86_64-pc-windows-msvc','-O1',
                            '-ffreestanding','-fno-stack-protector','-c',str(path/'test.c'),
                            '-o',str(path/'test.obj')],check=True,capture_output=True,text=True)
            subprocess.run([str(tc/'ld.lld.exe'),'-flavor','link','/entry:tests','/subsystem:console',
                            '/nodefaultlib',str(path/'test.obj'),'/out:'+str(path/'test.exe')],
                           check=True,capture_output=True,text=True)
            result = subprocess.run([str(path/'test.exe')])
            if result.returncode:
                (ROOT / 'build/ui-failed-native.c').write_text((path/'test.c').read_text())
            self.assertEqual(result.returncode,0,'native UI check failed at C line '+str(result.returncode))

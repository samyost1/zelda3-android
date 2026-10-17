# Mapeamento da interface PT-BR

ROM PT-BR: `D0D09ED41F9C373FE6AFDCCAFBF0DA8C88D3D90D`. Original: `6D4F10A8B10E10DBE624CB23CF03B88BB8252973`.

O manifesto contém somente endereços, tamanhos e hashes; nenhum recurso extraído. Os endereços são offsets de arquivo sem cabeçalho de copiador.

## Cobertura

| Área | Recursos / integração |
| --- | --- |
| Inventário e HUD | Nove tabelas de nomes/habilidades em hud.c; gráficos 69–6B |
| Seleção, criação, cópia e exclusão | Cinco stripes em nmi.c; quatro tabelas de confirmação em select_file.c; fonte original da tradução |
| Entrada de nome | Mesma tabela de caracteres e navegação US, auditada; fonte bruta da ROM PT-BR e mapa de 121 caracteres; códigos de nomes no SRAM permanecem US |
| Salvar/continuar e derrota | Diálogos já extraídos; derrota com nove letras e atributos por tile; novas tabelas em A0:8041/A0:8065 e 08:F5B4 |
| Abertura/apresentação | Gráficos alterados 05/08/68 e BGs; legend graphics de attract.c auditados sem mudanças |
| Mapas | Mapa global, stripes do mapa e tabelas de masmorras auditados sem mudanças; manter originais |
| Encerramento/créditos | Paleta por linha e bytes de tiles; offsets e fonte PT; legendas relocadas para $A0:80C8 |

## Adaptações de código do hack

- Ponteiros gráficos: seguir tabelas separadas de banco/alto/baixo em 4FF3/50D2/51B1 (sprites) e 4F80/505F/513E (BG). Comparar conteúdo descomprimido, pois quase todos os pacotes foram recomprimidos/relocados.
- Créditos: PT troca índices da tabela US por um byte de atributos/paleta por linha, seguido dos bytes de tiles. O motor expande as linhas em palavras de tile e usa 3CA9 como espaço. Os 394 offsets e todos os limites das 16 legendas foram conferidos com essa codificação.
- Legendas do encerramento: dados em 1000C8, delimitados pelos 17 offsets em 742E1; o bloco US em 73F4C permanece na ROM mas não é mais usado.
- A fonte de interface usa os tiles brutos de 70000; a fonte normalizada dos diálogos permanece separada.
- Não substituir layouts completos de inventário: preservar as extensões do port e trocar somente tabelas e gráficos traduzidos.

## Recursos alterados

| ID | Recurso | Offset PT | Bytes |
| --- | --- | --- | --- |
| 0001 | kHudAbilityText | 06F959 | 160 |
| 0002 | kHudGlovesText | 06F931 | 40 |
| 0003 | kHudBottlesItemText | 06F449 | 256 |
| 0004 | kHudMushroomItemText | 06F549 | 32 |
| 0005 | kHudFluteItemText | 06F569 | 64 |
| 0006 | kHudMirrorItemText | 06F5A9 | 32 |
| 0007 | kHudBowItemText | 06F5C9 | 96 |
| 0008 | kHudItemText | 06F1C9 | 640 |
| 0009 | kHudEquipmentDungeonItemText | 06ED09 | 32 |
| 000A | kCopyFile_SelectionAndBlinker_Tab | 06668D | 173 |
| 000B | kCopyFile_TargetSelectionAndBlink_Tab0 | 06673A | 133 |
| 000C | kCopyFile_TargetSelectionAndBlink_Tab2 | 06523A | 49 |
| 000D | kKILLFile_ChooseTarget_Tab2 | 06541E | 101 |
| 0105 | sprite_05 | 088E00 | 1536 |
| 0108 | sprite_08 | 08A000 | 1536 |
| 012D | sprite_2d | 0B27D6 | 514 |
| 0161 | sprite_61 | 0C10ED | 552 |
| 0168 | sprite_68 | 0C283D | 1173 |
| 0169 | sprite_69 | 0C2CD2 | 1299 |
| 016A | sprite_6a | 0A7636 | 1434 |
| 016B | sprite_6b | 0A7BD0 | 1636 |
| 0216 | background_16 | 091A64 | 1288 |
| 023D | background_3d | 09D300 | 1178 |
| 0241 | background_41 | 09E6CB | 1329 |
| 024D | background_4d | 0A1EE2 | 1331 |
| 0253 | background_53 | 0A3ABE | 1306 |
| 0271 | background_71 | 0A7636 | 1434 |
| 0272 | background_72 | 0A7BD0 | 1636 |
| 0363 | kBgTilemap_0 | 065D6D | 1115 |
| 0364 | kBgTilemap_1 | 0667BF | 1467 |
| 0365 | kBgTilemap_2 | 0662A8 | 177 |
| 0366 | kBgTilemap_3 | 06663C | 81 |
| 0367 | kBgTilemap_4 | 066456 | 233 |
| 0400 | InterfaceFont | 070000 | 4096 |
| 0401 | CreditsText | 073038 | 2028 |
| 0402 | CreditsOffsets | 07393D | 788 |
| 0403 | SceneCaptions | 1000C8 | 1074 |
| 0404 | SceneOffsets | 0742E1 | 34 |
| 0405 | NameFontMap | 077C09 | 363 |
| 0406 | GameOverCharacters | 100041 | 36 |
| 0407 | GameOverSweep | 0475B4 | 9 |
| 0408 | GameOverUnfurl | 100065 | 9 |

Hashes individuais e as 138 tabelas auditadas estão em `tools/translations/ptbr_ui_manifest.json`.

Reprodução: `python tools/translations/map_ui.py --us-rom <original> --translated-rom <ptbr>`.

## Validação no aparelho

Comparar título/apresentação; criar um nome e copiar/excluir arquivos; abrir inventário, mapas e menu de salvar; provocar derrota; conferir legendas finais e créditos. Repetir com tela cheia e telas trocadas. Carregar estados anteriores e conferir a próxima transição de tela. A inspeção dos dados não substitui essa validação visual.

## Pacote e compatibilidade

O pacote UI v1 tem assinatura Z3UIBR01, versão, contagem, SHA-1 da ROM reconhecida, tamanho, descritores [ID, offset, tamanho] e CRC32. A disposição, o tamanho e o CRC esperados são gerados do manifesto para Java e C. O motor copia o pacote uma vez para memória alinhada, pois os contêineres de idioma podem estar desalinhados.

O pacote é o terceiro bloco da entrada pt-br em kDialogueMap. É independente dos diálogos, fonte e recursos originais, mas é publicado no mesmo arquivo por uma única substituição atômica. Language = pt-br e um pacote válido são necessários; ausente, incompatível ou corrompido mantém a interface original.

A derrota passa de oito para nove letras e mantém os atributos de cada metade do glifo, incluindo espelhamento. Os nomes conservam a codificação US no SRAM; somente seu desenho consulta o mapa de 121 caracteres em 77C09.

Estados antigos não mudam de formato. Ao carregar, bancos identificados como gráficos antigos de interface são atualizados, preservando glifos personalizados de controles. Somente tiles que ainda coincidem com o original são substituídos; bancos com mais de oito tiles diferentes são preservados. Inventários completos, inclusive durante sua entrada/saída por rolagem, recebem os rótulos junto dos gráficos. Em estados antigos salvos durante a expansão de garrafas, menus de arquivo ou créditos, a interface original é mantida até o próximo redesenho completo, preservando a imagem e sua codificação juntas. A próxima abertura do inventário ou inicialização completa dos gráficos reativa PT-BR. Uma nova carga de estado PT-BR também reavalia essa decisão. A animação de derrota adapta a contagem de letras e seus gráficos sem mudar o progresso. Estados durante abertura, encerramento e animações ainda exigem conferência no aparelho.

A extensão NOT ASSIGNED do port, ausente na ROM, aparece como SEM ITEM em PT-BR. As atribuições extras de itens são preservadas.

## Reimportação na instalação de desenvolvimento

Fechar o jogo, fazer uma cópia de zelda3_assets.dat e remover somente esse arquivo de Android/data/com.dishii.zelda3/files. Abrir o app e selecionar novamente a ROM PT-BR suportada. Preservar zelda3.ini, saves e demais arquivos. Não desinstalar nem limpar os dados do aplicativo.

## Checklist do aparelho (pendente)

- Primeira importação somente com a ROM PT-BR; reiniciar e conferir persistência.
- Título e apresentação; seleção, cópia e exclusão de arquivos; cancelamentos e confirmações.
- Criar nome, carregar nome anterior, copiar e excluir arquivos de teste.
- Inventário: nomes, habilidades, luvas, equipamentos, garrafas, atribuições Y/X/L/R e SEM ITEM.
- HUD, diálogos, menu de salvar/continuar, derrota e mapas global/masmorras.
- Dezesseis legendas finais e rolagem dos créditos.
- Estados antigos e novos: automático, rápido e quatro manuais; inventário aberto e animações.
- Tela cheia e telas trocadas; repetir importação US em outra instalação para confirmar inglês.

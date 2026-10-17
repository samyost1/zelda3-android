package com.dishii.zelda3;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;

/** Android companion UI vocabulary. Keys are existing English display labels, never INI keys. */
final class SecondScreenText {
    static final Map<String, String> PORTUGUESE;
    static {
        Map<String, String> t = new LinkedHashMap<String, String>();
        String[][] pairs = {
            {"QUICK STATE", "ESTADO RÁPIDO"}, {"CLEAR", "LIMPAR"}, {"UNBOUND", "SEM BOTÃO"},
            {"TRANSFER BUTTON", "TRANSFERIR BOTÃO"}, {"TRANSFER", "TRANSFERIR"}, {"CANCEL", "CANCELAR"},
            {"CUSTOM BINDING", "MAPEAMENTO PERSONALIZADO"},
            {"EDIT IN INI", "EDITE NO INI"}, {"ERROR", "ERRO"}, {"OK", "OK"}, {"TO", "PARA"},
            {"GEAR", "EQUIPAMENTOS"}, {"MAP", "MAPA"}, {"ITEMS", "ITENS"},
            {"SETTINGS", "CONFIGURAÇÕES"}, {"BACK", "VOLTAR"},
            {"SAVE STATES", "ESTADOS SALVOS"}, {"REMAP BUTTONS", "MAPEAR BOTÕES"},
            {"SAVE STATE", "SALVAR ESTADO"}, {"LOAD STATE", "CARREGAR ESTADO"},
            {"AUTOSAVE", "SALVAMENTO AUTOMÁTICO"}, {"WIDESCREEN", "TELA CHEIA"},
            {"CRT TOP SCREEN", "CRT NA TELA SUPERIOR"}, {"CRT THIS SCREEN", "CRT NA TELA INFERIOR"},
            {"TOP SCREEN HUD", "INDICADORES NA TELA SUPERIOR"}, {"X ITEM RING", "ITENS DO X"},
            {"SWAP SCREENS", "TROCAR TELAS"}, {"MSU-1 MUSIC", "MÚSICA MSU-1"},
            {"ON", "LIGADO"}, {"OFF", "DESLIGADO"}, {"RESTART", "REINICIAR"},
            {"NO PACK", "SEM PACOTE"}, {"SAVED", "SALVO"}, {"LOADED", "CARREGADO"},
            {"EMPTY", "VAZIO"}, {"NO IMAGE", "SEM IMAGEM"}, {"SAVE", "SALVAR"},
            {"LOAD", "CARREGAR"}, {"SLOT", "ESPAÇO"}, {"PRESS KEY", "APERTE UM BOTÃO"},
            {"UP", "CIMA"}, {"DOWN", "BAIXO"}, {"LEFT", "ESQUERDA"}, {"RIGHT", "DIREITA"},
            {"HOLD TO PIN", "SEGURE PARA MARCAR"}, {"DUNGEON", "MASMORRA"},
            {"BOTTLES", "FRASCOS"}, {"PENDANTS", "PINGENTES"}, {"CRYSTALS", "CRISTAIS"},
            {"LIFE", "VIDA"}, {"MAGIC", "MAGIA"},
            {"ITEM SWITCH L R", "TROCAR ITEM COM L R"}, {"TURN WHILE DASH", "MUDAR DIREÇÃO NA CORRIDA"},
            {"MIRROR TO DARK", "ESPELHO PARA O MUNDO SOMBRIO"}, {"COLLECT BY SWORD", "COLETAR COM ESPADA"},
            {"SWORD BREAKS POTS", "QUEBRAR VASOS COM ESPADA"}, {"LOW HP BEEP", "ALERTA DE POUCA VIDA"},
            {"SKIP INTRO", "PULAR INTRODUÇÃO"}, {"MAX ITEMS YELLOW", "ITENS NO MÁXIMO EM AMARELO"},
            {"MORE BOMBS", "MAIS BOMBAS ATIVAS"}, {"CARRY 9999 RUPEES", "CARREGAR 9999 RÚPIAS"},
            {"CANCEL BIRD RIDE", "CANCELAR VIAGEM DO PÁSSARO"}, {"DIM FLASHES", "REDUZIR CLARÕES"},
            {"SEWERS", "ESGOTOS"}, {"HYRULE CASTLE", "CASTELO DE HYRULE"},
            {"EASTERN PALACE", "PALÁCIO DO LESTE"}, {"DESERT PALACE", "PALÁCIO DO DESERTO"},
            {"CASTLE TOWER", "TORRE DO CASTELO"}, {"SWAMP PALACE", "PALÁCIO DO PÂNTANO"},
            {"DARK PALACE", "PALÁCIO DAS TREVAS"}, {"MISERY MIRE", "PÂNTANO DA MISÉRIA"},
            {"SKULL WOODS", "BOSQUE DAS CAVEIRAS"}, {"ICE PALACE", "PALÁCIO DO GELO"},
            {"TOWER OF HERA", "TORRE DE HERA"}, {"THIEVES TOWN", "VILA DOS LADRÕES"},
            {"TURTLE ROCK", "ROCHA DA TARTARUGA"}, {"GANONS TOWER", "TORRE DE GANON"},
            {"JAN", "JAN"}, {"FEB", "FEV"}, {"MAR", "MAR"}, {"APR", "ABR"},
            {"MAY", "MAI"}, {"JUN", "JUN"}, {"JUL", "JUL"}, {"AUG", "AGO"},
            {"SEP", "SET"}, {"OCT", "OUT"}, {"NOV", "NOV"}, {"DEC", "DEZ"},
        };
        for (String[] pair : pairs) t.put(pair[0], pair[1]);
        PORTUGUESE = Collections.unmodifiableMap(t);
    }

    private final boolean portuguese;

    SecondScreenText(String language) {
        portuguese = language != null && "pt-br".equalsIgnoreCase(language.trim());
    }

    String get(String english) {
        String translated = portuguese ? PORTUGUESE.get(english) : null;
        return translated == null ? english : translated;
    }

    // Reserve for every possible state, so toggles and confirmations cannot resize labels.
    float settingValueWidth(String key) {
        String[] values;
        if ("SAVE STATES".equals(key) || "REMAP BUTTONS".equals(key)) return 0;
        if ("SAVE STATE".equals(key)) values = new String[]{"", "SAVED"};
        else if ("LOAD STATE".equals(key)) values = new String[]{"", "EMPTY", "LOADED"};
        else if ("SWAP SCREENS".equals(key)) values = new String[]{"ON", "OFF", "RESTART"};
        else if ("MSU-1 MUSIC".equals(key)) values = new String[]{"ON", "OFF", "RESTART", "NO PACK"};
        else values = new String[]{"ON", "OFF"};
        float width = 0;
        for (String value : values) width = Math.max(width, PixelText.width(get(value)));
        return width;
    }

    String gearTab() {
        return portuguese ? "EQUIP." : "GEAR";
    }
}

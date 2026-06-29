"""Teste rápido do sistema de análise de bancas"""
from modules.banca_area_analyzer import AREAS_CONHECIMENTO

print('✅ Módulo carregado com sucesso!')
print(f'\n📚 Total de áreas suportadas: {len(AREAS_CONHECIMENTO)}')
print('\n🏛️  Áreas disponíveis:')
for area in AREAS_CONHECIMENTO.keys():
    print(f'  • {area}')

print('\n✅ Sistema pronto para uso!')

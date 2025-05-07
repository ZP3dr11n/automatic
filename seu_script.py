import gspread
import requests
from oauth2client.service_account import ServiceAccountCredentials
import os

# Autenticação no Google Sheets usando OAuth 2.0
def authenticate_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('path_to_your_credentials.json', scope)
    client = gspread.authorize(creds)
    return client

# Função para obter o ID do cartão do Trello
def get_trello_card_id(ra_number):
    url = f'https://api.trello.com/1/search'
    params = {
        'query': str(ra_number),
        'key': os.getenv('TRELLO_KEY'),
        'token': os.getenv('TRELLO_TOKEN')
    }
    response = requests.get(url, params=params)
    cards = response.json().get('cards', [])
    for card in cards:
        if str(ra_number) in card['name']:
            return card['id']
    return None

# Função para mover o cartão para a lista correspondente
def move_card_to_list(card_id, status):
    status_to_list = {
        "AG. O SAS": "AGUARDANDO SAS",
        "SAS": "SAS",
        "CONCLUÍDO": "Feito"
    }

    list_name = status_to_list.get(status)
    if not list_name:
        print(f'Erro: Status "{status}" não mapeado.')
        return
    
    url = f'https://api.trello.com/1/boards/your_board_id/lists'
    params = {
        'key': os.getenv('TRELLO_KEY'),
        'token': os.getenv('TRELLO_TOKEN')
    }
    response = requests.get(url, params=params)
    lists = response.json()
    
    list_id = None
    for trello_list in lists:
        if trello_list['name'] == list_name:
            list_id = trello_list['id']
            break
    
    if list_id:
        url = f'https://api.trello.com/1/cards/{card_id}'
        data = {
            'idList': list_id,
            'key': os.getenv('TRELLO_KEY'),
            'token': os.getenv('TRELLO_TOKEN')
        }
        response = requests.put(url, params=data)
        if response.status_code == 200:
            print(f'Cartão movido para a lista "{list_name}".')
        else:
            print(f'Erro ao mover o cartão: {response.status_code}')
    else:
        print(f'Erro: Lista "{list_name}" não encontrada no Trello.')

# Função para verificar e atualizar o Trello quando o status mudar na planilha
def check_and_update_trello():
    client = authenticate_google_sheets()
    sheet = client.open('Nome_da_sua_planilha').sheet1
    records = sheet.get_all_records()
    
    for record in records:
        ra_number = record['RA']
        status = record['Status']
        
        if status:
            print(f'Atualizando RA {ra_number} para status "{status}".')
            card_id = get_trello_card_id(ra_number)
            if card_id:
                move_card_to_list(card_id, status)
            else:
                print(f'Erro: Cartão com RA {ra_number} não encontrado no Trello.')

# Chame a função principal
check_and_update_trello()

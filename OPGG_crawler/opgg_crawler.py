import requests
import shutil
import json
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import pandas as pd

champion_info = None
data_list=[]

username = 'zzzwon'

headers = {
     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

base_url = "https://www.op.gg/summoners/na/zzzwon-NA1"

def createTextFile(filename, content):
    file_path ="./"+filename+".txt"
    with open(file_path, 'w') as file:
        file.write(content)

def convertKRtoCT(KRtime):
    kst_time = datetime.strptime(KRtime, "%Y-%m-%dT%H:%M:%S%z")
    utc6_offset = timedelta(hours=-6)
    ct_time = kst_time - utc6_offset
    ct_time_str = ct_time.strftime("%Y-%m-%dT%H:%M:%S")
    return ct_time_str

def convertDuration(total_seconds):
    # 초를 시, 분, 초로 분리
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    # 시:분:초 형식의 문자열로 변환
    time_str = "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)

    return time_str

def getChampionName(targetId):
    for each in champion_info:
        if each['id']==targetId:
            return each['key']
        
# 엑셀 파일을 불러오기
try:
    existing_df = pd.read_excel('./test_excel.xlsx')
    original_excel_path = './test_excel.xlsx'
    backup_excel_path = './test_excel_backup.xlsx'
    shutil.copyfile(original_excel_path, backup_excel_path)
except FileNotFoundError:
    # 파일이 없으면 빈 DataFrame 생성
    existing_df = pd.DataFrame()

print('existing df 체크')
print(existing_df.columns)

try:
    response = requests.get(base_url, headers=headers)

    # 서버의 응답이 성공적이라면
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        pretty_html = soup.prettify()

        createTextFile('entire_soup',pretty_html)

        next_data_script = soup.select_one('script#__NEXT_DATA__')
        createTextFile('next_data',next_data_script.prettify())
        
        # JSON 데이터를 문자열로
        json_data = next_data_script.string

        # JSON data parsing
        data = json.loads(json_data)
        createTextFile('parsed_json',json.dumps(data, indent=4))

        #game history data
        match_data = data['props']['pageProps']['games']['data']
        createTextFile('match_data',json.dumps(match_data,indent=4))

        #champion info
        champion_info = data['props']['pageProps']['data']['champions']

        for each_match in match_data :

            #Ranked Solo/Duo game history only
            if each_match['queue_info']['queue_translate'] == 'Ranked Solo/Duo':
                
                #Game play date (KR time) (EX_date_part, EX_time_part)
                record_KST = each_match['created_at']
                record_CT = convertKRtoCT(record_KST)

                    #parse date and time #SS
                EX_date_part, EX_time_part = record_CT.split("T")

                #Match unique code
                    #use date and time to avoid same data

                #Game duration (EX_duration)
                EX_duration = convertDuration(each_match['game_length_second'])

                #Win or Lose (EX_result)
                participants = each_match['participants']
                for p in participants :
                    user = p['summoner']['game_name']

                    #get history of a specific user only
                    if user == 'zzzwon':
                        stats = p['stats']
                        EX_result = stats['result']
                
                #EX_Position
                        EX_position = p['position']
                
                #EX_Champion
                        EX_champion = getChampionName(p['champion_id'])
                
                #EX_teamkey
                        EX_teamkey = p['team_key']
                
                #KDA
                        EX_kill = stats['kill']
                        EX_death = stats['death']
                        EX_assist = stats['assist']

                #cal KDA
                        if EX_death==0:
                            EX_formatted_KDA = 'Perfect Game'
                        else :
                            cal_KDA = (EX_kill + EX_assist)/EX_death
                            EX_formatted_KDA = "{:.2f}".format(cal_KDA)

                #Minion
                        EX_minions = stats['minion_kill']
                
                #Minion per minute (EX_minions_per_minute_rounded)
                        total_minutes = each_match['game_length_second'] / 60
                        minions_per_minute = EX_minions / total_minutes
                        EX_minions_per_minute_rounded = round(minions_per_minute, 1)
                
                #Gold
                        EX_gold = stats['gold_earned']

                #Gold per min (EX_gold_per_minute_rounded)
                        gold_per_minute = EX_gold / total_minutes
                        EX_gold_per_minute_rounded = int(gold_per_minute)

                #Vision Score
                        EX_vision_score = stats['vision_score']
                
                #Control Ward purchse
                        EX_control_ward_purchse = stats['vision_wards_bought_in_game']
                
                #ward placed
                        EX_ward_placed = stats['ward_place']
                
                #ward erased
                        EX_ward_kill = stats['ward_kill']
                
                #Total damage dealt to enemy
                        EX_damage_to_champion = stats['total_damage_dealt_to_champions']
                
            temp_dict={
                # 'Date' : EX_date_part,
                # 'Time' : EX_time_part,
                'Date' : record_CT,
                'Duration' : EX_duration,
                'Win or Lose' : EX_result,
                'Position' : EX_position,
                'Champion' : EX_champion,
                'Team Side' : EX_teamkey,
                'Kill' : EX_kill,
                'Death' : EX_death,
                'Assist' : EX_assist,
                'KDA' : EX_formatted_KDA,
                'Total minions' : EX_minions,
                'Minions per minute' : EX_minions_per_minute_rounded,
                'Gold earned' : EX_gold,
                'Gold earn per minute' :EX_gold_per_minute_rounded,
                'Vision Score' : EX_vision_score,
                'Control Ward Purchase' : EX_control_ward_purchse,
                'Ward placed' : EX_ward_placed,
                'Ward erased' : EX_ward_kill,
                'Total damage to champions' : EX_damage_to_champion
            }

            data_list.append(temp_dict)
    
        new_df = pd.DataFrame(data_list)
        new_df = new_df.drop_duplicates(subset='Date', keep='first')
        excel_path = './test_excel.xlsx'
        new_df.to_excel(excel_path, index=False)
        print(f"Saved Excel file at {excel_path}")

        for index, row in new_df.iterrows():
        # existing_df가 비어 있거나 'Date' 열이 없는 경우, 바로 데이터를 추가합니다.
            if 'Date' not in existing_df.columns or existing_df.empty:
                existing_df = existing_df.append(row, ignore_index=True)
            else:
                # existing_df에 'Date' 열이 있는 경우, 중복을 확인하고 추가합니다.
                if row['Date'] not in existing_df['Date'].values:
                    existing_df = existing_df.append(row, ignore_index=True)

        #변경된 DataFrame을 엑셀 파일로 저장
        excel_path = './test_excel.xlsx'
        existing_df.to_excel(excel_path, index=False)
        print(f"Updated Excel file at {excel_path}")


    else:
        print(f"Error fetching the page: Status code {response.status_code}")
except Exception as e:
    print(f"An error occurred: {e}")

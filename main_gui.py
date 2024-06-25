from flask import Flask, render_template, request, jsonify
from collections import defaultdict

app = Flask(__name__)

def create_graph(stations):
    graph = defaultdict(list)
    for line, stops in stations.items():
        for i in range(len(stops) - 1):
            graph[stops[i]].append((stops[i+1], line))
            graph[stops[i+1]].append((stops[i], line))
    return graph

def find_optimal_route(graph, start, end, via_stations=None, max_transfers=4):
    def dfs(current, path, transfers, lines_used, transfer_info):
        if current == end and (not via_stations or all(station in path for station in via_stations)):
            return path, transfer_info

        if transfers > max_transfers or len(path) > len(graph):  # 追加：無限ループ防止
            return None, None

        best_path, best_transfer_info = None, None
        for next_station, line in graph[current]:
            if next_station in path:  # 同じ駅を二度通らない
                continue
            new_transfers = transfers
            new_transfer_info = transfer_info.copy()
            if not lines_used or line != lines_used[-1]:
                new_transfers += 1
                if transfers > 0:
                    new_transfer_info.append((current, lines_used[-1], line))
            new_path, new_info = dfs(next_station, path + [next_station], new_transfers, lines_used + [line], new_transfer_info)
            if new_path and (not best_path or len(new_path) > len(best_path)):  # 最長ルートを選択
                best_path, best_transfer_info = new_path, new_info

        return best_path, best_transfer_info

    return dfs(start, [start], 0, [], [])

def optimize_route(stations, start=None, end=None, via_stations=None):
    graph = create_graph(stations)
    all_stations = set(station for line in stations.values() for station in line)
    
    terminal_stations = {'藤が丘', '高畑', '徳重', '太閤通', '上飯田', '名古屋港'}
    terminal_stations.update(stations['M'])  # 名城線の駅を追加

    if start is None:
        start_stations = terminal_stations
    else:
        start_stations = [start]

    if end is None:
        end_stations = terminal_stations
    else:
        end_stations = [end]

    best_route, best_transfer_info = None, None
    for s in start_stations:
        for e in end_stations:
            if s != e:
                route, transfer_info = find_optimal_route(graph, s, e, via_stations)
                if route and (not best_route or len(route) > len(best_route)):  # 最長ルートを選択
                    best_route, best_transfer_info = route, transfer_info

    return best_route, best_transfer_info

stations = {
    'H': ['藤が丘', '本郷', '上社', '一社', '星ヶ丘', '東山公園', '本山',
           '覚王山','池下','今池', '千種','新栄町', '栄',  '伏見', '名古屋',
           '亀島','本陣','中村日赤','中村公園','岩塚', '八田', '高畑'],
    'M': ['大曽根', 'ナゴヤドーム前矢田', '砂田橋', '茶屋ヶ坂', '自由が丘', '本山', '名古屋大学',
          '八事日赤', '八事', '総合リハビリセンター', '瑞穂運動場東', '新瑞橋', '妙音通',
          '堀田', '熱田神宮伝馬町', '熱田神宮西', '西高蔵', '金山', '東別院', '上前津', '矢場町', '栄',
          '久屋大通', '名古屋城', '名城公園','黒川', '志賀本通', '平安通', '大曽根'],
    'S': ['徳重', '神沢', '相生山', '鳴子北', '野並', '鶴里', '桜本町', '新瑞橋',
          '瑞穂運動場西', '瑞穂区役所', '桜山', '御器所', '吹上', '今池', '車道', 
          '高岳', '久屋大通', '丸の内','国際センター', '名古屋', '太閤通'],
    'T': ['赤池', '平針', '原', '植田', '塩釜口', '八事', 'いりなか', '川名',
          '御器所', '荒畑', '鶴舞', '浄心', '庄内通', '庄内緑地公園', '上小田井'],
    'K': ['上飯田', '平安通'],
    'E': ['金山','日比野', '六番町', '東海通', '港区役所', '築地口','名古屋港']
}

lines = {
    'H': '東山線', 'M': '名城線', 'S': '桜通線',
    'T': '鶴舞線', 'K': '上飯田線', 'E': '名港線'
}

@app.route('/')
def index():
    all_stations = sorted(set(station for line in stations.values() for station in line))
    return render_template('index.html', stations=all_stations)

@app.route('/optimize', methods=['POST'])
def optimize():
    start = request.form.get('start') or None
    end = request.form.get('end') or None
    via = request.form.get('via')
    
    via_stations = [station.strip() for station in via.split(',')] if via else None

    optimal_route, transfer_info = optimize_route(stations, start=start, end=end, via_stations=via_stations)

    if optimal_route:
        result = {
            "route": ' -> '.join(optimal_route),
            "total_stations": len(optimal_route),
            "transfers": [
                f"{station}駅: {lines[from_line]}から{lines[to_line]}に乗り換え"
                for station, from_line, to_line in transfer_info
            ]
        }
        return jsonify(result)
    else:
        return jsonify({"error": "有効なルートが見つかりませんでした。"})

if __name__ == '__main__':
    app.run(debug=True)
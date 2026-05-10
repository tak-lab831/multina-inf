import os
import pandas as pd
import itertools
from flask import Flask, render_template, request, redirect, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "lab_secret_key"  # フラッシュメッセージ用

# Ubuntu上の実行ファイルの場所を基準に絶対パスを作成
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 保存フォルダがない場合は作成
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- 解析ロジック関数 ---
def analyze_csv(file_path, threshold):
    # GUIのロジックを継承（Shift-JIS対応）
    df00 = pd.read_csv(file_path, header=0, encoding='shift_jis')
    
    # ラダー(X)を除外、未検出(-)を除外
    df01 = df00.loc[~df00['ウェル名'].str.contains('X'), ['ウェル名', 'サイズ(bp)/(nt)']]
    df02 = df01[df01['サイズ(bp)/(nt)'] != '-']
    
    # ウェルごとにサイズをリスト化
    df03 = df02.groupby('ウェル名')['サイズ(bp)/(nt)'].agg(list).reset_index()

    # 1500以下のフィルタリング
    def filter_val(x):
        if isinstance(x, list):
            return [int(float(i)) for i in x if str(i).replace('.','',1).isdigit() and float(i) <= 1500]
        return []

    df03.iloc[:, 1] = df03.iloc[:, 1].apply(filter_val)
    # 空になった行を削除
    df03 = df03[df03.iloc[:, 1].map(len) > 0].reset_index(drop=True)

    # 近い値の組み合わせ抽出
    valid_comb = []
    well_names = df03['ウェル名'].tolist()
    size_data = df03.iloc[:, 1].tolist()

    for i, j in itertools.combinations(range(len(size_data)), 2):
        row1, row2 = size_data[i], size_data[j]
        if len(row1) == len(row2):
            if all(abs(x - y) <= threshold for x, y in zip(row1, row2)):
                valid_comb.append((well_names[i], well_names[j]))

    # 重複・共通要素をまとめるマージ処理
    def merge_to_groups(pairs):
        groups = [set(p) for p in pairs]
        merged = True
        while merged:
            merged = False
            new_groups = []
            while groups:
                current = groups.pop(0)
                for i, other in enumerate(groups):
                    if current.intersection(other):
                        current.update(other)
                        groups.pop(i)
                        merged = True
                        break
                new_groups.append(current)
            groups = new_groups
        return [sorted(list(g)) for g in groups]

    merged_groups = merge_to_groups(valid_comb)
    
    # フラットなリスト（単独判定用）
    all_grouped_wells = [well for group in merged_groups for well in group]
    
    # 1. 単独試料の抽出
    alone_df = df03[~df03['ウェル名'].isin(all_grouped_wells)]
    alone_list = alone_df.to_dict('records')

    # 2. グループ詳細の抽出
    grouped_results = []
    for group in merged_groups:
        details = df03[df03['ウェル名'].isin(group)].to_dict('records')
        grouped_results.append({
            'names': " / ".join(group),
            'details': details
        })

    return alone_list, grouped_results

# --- ルート定義 ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # ファイルチェック
        if 'file' not in request.files:
            flash("ファイルが見つかりません")
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash("ファイルが選択されていません")
            return redirect(request.url)

        # しきい値取得
        try:
            threshold = int(request.form.get('threshold', 20))
        except ValueError:
            threshold = 20

        # 保存と解析
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)

        try:
            alone, grouped = analyze_csv(save_path, threshold)
            return render_template('index.html', alone=alone, grouped=grouped, threshold=threshold)
        except Exception as e:
            flash(f"解析中にエラーが発生しました: {e}")
            return redirect(request.url)
        finally:
            os.remove(save_path)
            pass

    return render_template('index.html', alone=None, grouped=None)

if __name__ == '__main__':
    # 開発用（直接実行時）
    app.run(host='0.0.0.0', port=5000, debug=True)

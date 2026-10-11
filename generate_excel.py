import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def create_timeout_workbook(filename="AWS_Timeout_Architecture_Recommendation.xlsx"):
    wb = openpyxl.Workbook()
    
    # ----------------------------------------------------
    # Monotone Palette & Styles (Meiryo UI)
    # ----------------------------------------------------
    FONT_FAMILY = "Meiryo UI"
    
    font_title = Font(name=FONT_FAMILY, size=16, bold=True, color="1E272E")
    font_subtitle = Font(name=FONT_FAMILY, size=11, italic=True, color="485460")
    font_sec_header = Font(name=FONT_FAMILY, size=12, bold=True, color="FFFFFF")
    font_tbl_header = Font(name=FONT_FAMILY, size=10, bold=True, color="FFFFFF")
    font_sub_header = Font(name=FONT_FAMILY, size=10, bold=True, color="2D3436")
    font_data = Font(name=FONT_FAMILY, size=9.5, color="2D3436")
    font_data_bold = Font(name=FONT_FAMILY, size=9.5, bold=True, color="2D3436")
    font_note = Font(name=FONT_FAMILY, size=8.5, color="636E72")
    
    # Monotone Fills
    fill_sec_dark = PatternFill(start_color="2D3436", end_color="2D3436", fill_type="solid")     # Jet charcoal
    fill_tbl_header = PatternFill(start_color="3B4252", end_color="3B4252", fill_type="solid")   # Dark slate
    fill_sub_header = PatternFill(start_color="E5E9F0", end_color="E5E9F0", fill_type="solid")   # Cool light gray
    fill_zebra = PatternFill(start_color="F8F9FB", end_color="F8F9FB", fill_type="solid")        # Very subtle light gray
    fill_white = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    fill_callout = PatternFill(start_color="ECEFF4", end_color="ECEFF4", fill_type="solid")      # Slate tint
    fill_accent_gray = PatternFill(start_color="D8DEE9", end_color="D8DEE9", fill_type="solid")  # Medium soft gray
    
    # Borders
    thin_border_side = Side(style='thin', color="D8DEE9")
    thick_border_side = Side(style='medium', color="4C566A")
    double_border_side = Side(style='double', color="2E3440")
    
    border_cell = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    border_header = Border(left=thin_border_side, right=thin_border_side, top=thick_border_side, bottom=thick_border_side)
    border_summary = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=double_border_side)
    
    # Alignments
    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    align_left = Alignment(horizontal="left", vertical="center", wrap_text=True)
    align_right = Alignment(horizontal="right", vertical="center", wrap_text=True)
    align_header = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # =========================================================================
    # SHEET 1: 1_全体設計原則と黄金律 (Golden Rules & Architecture)
    # =========================================================================
    ws1 = wb.active
    ws1.title = "1_全体設計原則と黄金律"
    ws1.views.sheetView[0].showGridLines = True
    
    # Title Block
    ws1["A1"] = "AWS・DB・APサーバ エンドツーエンド タイムアウト設計ガイドライン"
    ws1["A1"].font = font_title
    ws1["A2"] = "クライアントブラウザ 〜 API Gateway 〜 ECS(JBoss EAP 8.1) / EC2(Javaバッチ) 〜 RDS Proxy 〜 Aurora MySQL 8.4"
    ws1["A2"].font = font_subtitle
    
    ws1.row_dimensions[1].height = 28
    ws1.row_dimensions[2].height = 20
    ws1.row_dimensions[4].height = 26
    
    # Section 1 Header
    ws1.merge_cells("A4:G4")
    ws1["A4"] = "【最重要原則】タイムアウト設計における「2つの異なる黄金律（不等式）」"
    ws1["A4"].font = font_sec_header
    ws1["A4"].fill = fill_sec_dark
    ws1["A4"].alignment = align_left
    
    rule_texts = [
        ("原則1: アイドル・接続破棄タイムアウト（切断のチキンレース防止）",
         "【黄金律】 クライアント接続プール < プロキシ (RDS Proxy) < データベース (Aurora)",
         "Client Pool Idle Timeout (JBoss: 10分) < RDS Proxy IdleClientTimeout (30分) < MySQL wait_timeout (8時間)",
         "■ 理由: 誰が先に接続を捨てるべきか？\n"
         "・手前（クライアント側の接続プール）が自発的に古くなったコネクションを破棄(FIN)して再接続すべきです。\n"
         "・もしDBやProxy側が先にサイレント切断すると、クライアントは「まだ繋がっている」と誤認し、次のリクエストで死んだソケットにクエリを送信して「Communications link failure」や「Connection reset by peer」等の致命的障害が発生します。"),
         
        ("原則2: リクエスト・クエリ処理タイムアウト（ゾンビクエリ・リソース浪費防止）",
         "【黄金律】 DBクエリ実行制限 < JDBCソケット待機 < APトランザクション < ALB待機 < API Gateway (29秒)",
         "Aurora max_execution_time (15秒) < JDBC socketTimeout (20秒) < JBoss Tx Timeout (25秒) < ALB (60秒) < API GW (29秒)",
         "■ 理由: 誰が先にギブアップすべきか？\n"
         "・API Gateway REST APIの絶対制限である『29秒』以内に業務例外として綺麗にロールバックしてクライアントにJSON返却する必要があります。\n"
         "・もし下流(DB/JDBC)のタイムアウトがAPI GWより長いと、API GWが先に504を切断した後も、裏でAuroraがクエリを実行し続け(ゾンビクエリ)、Serverless v2のACUを無駄喰いし、行ロックを抱えて後続リクエストを詰まらせるカスケード障害を引き起こします。")
    ]
    
    curr_row = 6
    for title, formula, example, desc in rule_texts:
        ws1.merge_cells(start_row=curr_row, start_column=1, end_row=curr_row, end_column=7)
        c = ws1.cell(row=curr_row, column=1, value=title)
        c.font = font_sub_header
        c.fill = fill_sub_header
        c.alignment = align_left
        ws1.row_dimensions[curr_row].height = 24
        curr_row += 1
        
        ws1.merge_cells(start_row=curr_row, start_column=1, end_row=curr_row, end_column=7)
        c = ws1.cell(row=curr_row, column=1, value=formula)
        c.font = font_data_bold
        c.fill = fill_callout
        c.alignment = align_left
        ws1.row_dimensions[curr_row].height = 22
        curr_row += 1
        
        ws1.merge_cells(start_row=curr_row, start_column=1, end_row=curr_row, end_column=7)
        c = ws1.cell(row=curr_row, column=1, value=f"設定値イメージ: {example}")
        c.font = font_data_bold
        c.fill = fill_zebra
        c.alignment = align_left
        ws1.row_dimensions[curr_row].height = 20
        curr_row += 1
        
        ws1.merge_cells(start_row=curr_row, start_column=1, end_row=curr_row, end_column=7)
        c = ws1.cell(row=curr_row, column=1, value=desc)
        c.font = font_data
        c.fill = fill_white
        c.alignment = align_left
        ws1.row_dimensions[curr_row].height = 65
        curr_row += 2

    # Section 2: Architecture Flow Overview Table
    ws1.merge_cells(start_row=curr_row, start_column=1, end_row=curr_row, end_column=7)
    c = ws1.cell(row=curr_row, column=1, value="【システム構成要素と通過レイヤーの役割概要】")
    c.font = font_sec_header
    c.fill = fill_sec_dark
    c.alignment = align_left
    ws1.row_dimensions[curr_row].height = 26
    curr_row += 1
    
    headers_flow = ["#", "コンポーネント", "レイヤー", "プロトコル / 役割", "主なタイムアウトパラメータ", "タイムアウト発生時の挙動", "設計上の注意点"]
    for col_idx, h in enumerate(headers_flow, 1):
        cell = ws1.cell(row=curr_row, column=col_idx, value=h)
        cell.font = font_tbl_header
        cell.fill = fill_tbl_header
        cell.alignment = align_header
        cell.border = border_header
    ws1.row_dimensions[curr_row].height = 28
    curr_row += 1
    
    flow_data = [
        ("1", "クライアントブラウザ", "Client (L7)", "HTTPS / ユーザ操作", "ブラウザ fetch/axios timeout", "UI側で「通信タイムアウト」表示", "API Gatewayの29秒より少し長め(30〜35秒)に設定し、GWのエラーJSONを受け取る"),
        ("2", "API Gateway (REST API)", "AWS Gateway (L7)", "HTTPS / API公開", "Integration Timeout (統合タイムアウト)", "HTTP 504 Gateway Timeout を即返却", "ハードリミット29秒。オンライン系全体の最上限天井となる絶対境界線"),
        ("3", "VPC Link v2 (NLB/ALB)", "Network (L4/L7)", "Private Integration", "Integration Timeoutに包含", "通信トンネル切断", "API GatewayとVPC内リソースを繋ぐプライベートブリッジ"),
        ("4", "GWLBE / GWLB", "Network (L3/L4)", "GENEVE / トラフィック透過", "TCP Idle Timeout (デフォルト350秒)", "セッションテーブル破棄", "パケットを検査用Palo Altoへルーティング。セッションタイムアウトはALBより長いため問題なし"),
        ("5", "Palo Alto (VM-Series)", "Security (L4-L7)", "次世代ファイアウォール(IDS/IPS)", "TCP Established Session (3600秒)", "TCP RST / サイレントドロップ", "通信検査実施。ALB/JBossのキープアライブより十分に長い値(デフォルト1時間)を維持"),
        ("6", "ALB (Application LB)", "AWS LB (L7)", "HTTP/2, HTTP/1.1 リバースプロキシ", "Idle Timeout (デフォルト60秒)", "HTTP 504 (自身起因) / 502 (裏起因)", "ECS JBossのKeep-Aliveより「短く」設定することが絶対条件(502レースコンディション防止)"),
        ("7", "ECS Fargate (JBoss EAP 8.1)", "AP Server (L7)", "OpenJDK 21 / Jakarta EE 10", "Undertow Keep-Alive / Tx Timeout / JNDI Pool", "Txロールバック / 500または504返却", "Undertow keep-aliveはALB(60秒)より長い65秒。Txタイムアウトは25秒でフェイルファスト"),
        ("8", "EC2 バッチサーバ", "Batch Server", "OpenJDK 21 / Java standalone", "Connector/J (socketTimeout, connectTimeout)", "SQLException (SocketTimeoutException)", "オンライン資材をjavaコマンドで直接実行。JNDIは使えずJDBC接続プロパティで個別制御"),
        ("9", "RDS Proxy", "DB Proxy (L7)", "MySQLプロトコル プロキシ", "IdleClientTimeout(1800s), BorrowTimeout(120s)", "借用タイムアウト時 エラー返却", "オンラインの急激なスパイクからAuroraを保護。バッチはピニングや長時間占有に厳重注意"),
        ("10", "Aurora Serverless v2", "Database", "MySQL 8.4.7 LTS", "wait_timeout, max_execution_time, lock_wait", "Error 3024 (クエリ中断), ロック待ち解除", "オンラインはmax_execution_time(15秒)でゾンビクエリ殺害。バッチは無制限(0)で完走させる")
    ]
    
    for row_idx, data in enumerate(flow_data, curr_row):
        is_zebra = (row_idx % 2 == 0)
        for col_idx, val in enumerate(data, 1):
            cell = ws1.cell(row=row_idx, column=col_idx, value=val)
            cell.font = font_data_bold if col_idx in [1, 2] else font_data
            cell.fill = fill_zebra if is_zebra else fill_white
            cell.border = border_cell
            cell.alignment = align_center if col_idx in [1, 3] else (align_left if col_idx in [2, 4, 6, 7] else align_left)
        ws1.row_dimensions[row_idx].height = 36
        curr_row = row_idx + 1

    # =========================================================================
    # SHEET 2: 2_タイムアウト推奨値一覧 (Master Parameter Comparison Table)
    # =========================================================================
    ws2 = wb.create_sheet(title="2_タイムアウト推奨値一覧")
    ws2.views.sheetView[0].showGridLines = True
    
    ws2["A1"] = "タイムアウト設定値 マスタ比較一覧表（デフォルト値 vs 推奨値）"
    ws2["A1"].font = font_title
    ws2["A2"] = "AWS, MySQL 8.4.7 LTS, JBoss EAP 8.1, OpenJDK 21 / Java Connector/J 網羅比較"
    ws2["A2"].font = font_subtitle
    
    ws2.row_dimensions[1].height = 28
    ws2.row_dimensions[2].height = 20
    ws2.row_dimensions[4].height = 30
    
    headers_master = [
        "レイヤー / 対象",
        "コンポーネント",
        "設定パラメータ名",
        "タイムアウト分類",
        "単位",
        "デフォルト値",
        "オンライン推奨値",
        "バッチ推奨値",
        "不等式・依存関係",
        "設定場所 / 制御方式",
        "推奨理由 / 障害防止メカニズム (動作原理)"
    ]
    
    for col_idx, h in enumerate(headers_master, 1):
        cell = ws2.cell(row=4, column=col_idx, value=h)
        cell.font = font_tbl_header
        cell.fill = fill_tbl_header
        cell.alignment = align_header
        cell.border = border_header
        
    master_rows = [
        # Client & Ingress
        ("クライアント", "ブラウザ / Axios", "request timeout", "処理実行監視", "秒", "0 (無制限)", "35 秒", "N/A (画面なし)", "クライアント > API GW (29s)", "Axios/Fetch設定", "API Gatewayが29秒で返すJSON形式の504エラーをブラウザが確実に受け取れるよう、GWより少し長めに設定。"),
        ("Ingress / API", "API Gateway REST API", "Integration Timeout", "処理実行監視", "秒", "29 秒 (固定/上限)", "29 秒", "N/A (直接接続)", "API GW >= ALB > Tx", "API Gateway メソッド統合設定", "REST APIの絶対的な壁。これを超えるリクエストは強制切断され、即座にHTTP 504が返却される。"),
        ("Network / FW", "GWLB / GWLBE", "TCP Idle Timeout", "接続維持(L4)", "秒", "350 秒", "350 秒 (デフォルト維持)", "N/A", "GWLB > ALB Idle (60s)", "GWLB 属性設定", "通信パケットが流れない状態でのセッション維持時間。ALBの60秒より長いため途中でセッションが蒸発しない。"),
        ("Security", "Palo Alto Networks", "TCP Established Timeout", "接続維持(L4)", "秒", "3600 秒 (1時間)", "3600 秒 (デフォルト維持)", "3600 秒", "FW > 各種Keep-Alive", "PAN-OS セッション設定", "ファイアウォールのステートフルテーブル維持時間。十分長いため正当なキープアライブ接続が誤破棄されない。"),
        ("Security", "Palo Alto Networks", "TCP SYN / Handshake Timeout", "接続確立(L4)", "秒", "5 秒", "5 秒 (デフォルト維持)", "5 秒", "SYN < ALB TargetTimeout", "PAN-OS セッション設定", "TCP 3ウェイハンドシェイク確立までの待機時間。"),
        ("Ingress / LB", "ALB (Application LB)", "Idle Timeout", "接続維持(L7)", "秒", "60 秒", "60 秒 (または30秒)", "N/A", "ALB Idle < AP KeepAlive (65s)", "ALB 属性設定 (idle_timeout.timeout_seconds)", "クライアントおよびターゲットとの無通信監視。後続ECS JBossのKeep-Alive(65秒)より短くすることが502防止の絶対条件。"),
        
        # AP Server (JBoss EAP 8.1)
        ("AP Server", "JBoss EAP 8.1 (Undertow)", "keep-alive-timeout", "接続維持(L7)", "ミリ秒", "60000 (60秒)", "65000 (65秒)", "N/A (コンテナ外)", "Undertow Keep-Alive > ALB Idle (60s)", "standalone.xml (<http-listener>)", "ALBとJBoss間のレースコンディション防止。ALBが新規リクエストを転送した瞬間にJBossが切断する502 Bad Gatewayを防ぐ。"),
        ("AP Server", "JBoss EAP 8.1 (Undertow)", "no-request-timeout", "接続維持(L7)", "ミリ秒", "60000 (60秒)", "65000 (65秒)", "N/A", "Undertow > ALB", "standalone.xml (<http-listener>)", "リクエスト未着時のソケットクローズ時間。"),
        ("AP Server", "JBoss EAP 8.1 (Undertow)", "request-timeout", "処理実行監視", "ミリ秒", "0 (無制限)", "28000 (28秒)", "N/A", "Undertow Request < API GW (29s)", "standalone.xml (<http-listener>)", "リクエスト受付からレスポンス送信完了までの待機。API GWが切断する直前にAP側で検知可能にする。"),
        ("AP Server", "JBoss EAP 8.1 (JTA Tx)", "default-timeout", "処理実行監視", "秒", "300 秒 (5分)", "25 秒", "1800〜3600 秒 (業務要件別)", "JTA Tx < API GW (29s)", "standalone.xml (<coordinator-environment>)", "JTAグローバルトランザクション全体の制限。25秒でロールバックさせ、API GWの29秒切断前にアプリからエラーレスポンスを返す。"),
        ("AP Server / JNDI", "JBoss EAP 8.1 (IronJacamar)", "idle-timeout-minutes", "接続維持(Pool)", "分", "15 分 (900秒)", "10 分 (600秒)", "N/A (スタンドアロン)", "JBoss Pool < RDS Proxy Idle (30分)", "standalone.xml (<datasource> <pool>)", "【黄金律】クライアント接続プールがRDS Proxy(30分)より先に自発的に死んだ接続を破棄し、サイレント切断によるエラーを防止。"),
        ("AP Server / JNDI", "JBoss EAP 8.1 (IronJacamar)", "blocking-timeout-millis", "プール待機", "ミリ秒", "30000 (30秒)", "5000 (5秒)", "30000 (30秒)", "Blocking < Tx Timeout", "standalone.xml (<datasource> <timeout>)", "コネクションプールが枯渇した際の借用待ち時間。オンラインで30秒待つとAPI GW(29s)で即死するため、5秒で即座に枯渇エラーを返してフェイルファスト。"),
        ("AP Server / JNDI", "JBoss EAP 8.1 (IronJacamar)", "query-timeout", "処理実行監視", "秒", "0 (無制限)", "20 秒", "0 (個別指定/無制限)", "Query Timeout < JTA Tx (25s)", "standalone.xml (<datasource> <timeout>)", "JDBCステートメントのタイムアウト。SQL単体の上限を20秒に制限し、トランザクション上限(25秒)に余裕を持たせる。"),
        ("AP Server / JNDI", "JBoss EAP 8.1 (IronJacamar)", "set-tx-query-timeout", "処理連携", "Boolean", "false", "true", "N/A", "残り時間をクエリに反映", "standalone.xml (<datasource> <timeout>)", "JTAトランザクションの残り時間(例: 25秒 - 経過時間)を自動的にJDBC StatementのqueryTimeoutに引き継ぐ極めて有効な設定。"),
        ("AP Server / JNDI", "JBoss EAP 8.1 (IronJacamar)", "background-validation-millis", "死活監視", "ミリ秒", "0 (無効)", "60000 (60秒)", "N/A", "検証間隔 < Pool Idle", "standalone.xml (<datasource> <validation>)", "アイドル接続の生存確認。validate-on-match=falseと併用し、高頻度なCOM_PING/SELECT 1によるRDS Proxy負荷とピニング誤認を防止。"),

        # Java Connector/J (JDBC Driver)
        ("Java / JDBC", "MySQL Connector/J", "connectTimeout", "接続確立(L4)", "ミリ秒", "30000 (30秒)", "5000 (5秒)", "10000 (10秒)", "connectTimeout < BlockingWait", "接続プロパティ / URLパラメータ", "TCP接続およびSSLハンドシェイクの待機。ハングしたエンドポイントへの接続試行を素早く見切り、リトライや別AZ接続を促す。"),
        ("Java / JDBC", "MySQL Connector/J", "socketTimeout", "処理実行監視", "ミリ秒", "0 (無制限 / 永久ブロック)", "20000 (20秒)", "600000 (10分) または 0", "socketTimeout < API GW (29s)", "接続プロパティ (JBoss connection-property / URL)", "【極めて重要】デフォルト0は永久ブロック！ネットワーク障害やDBストール時にスレッドが永遠に死ぬのを防ぐ防波堤。バッチは長時間処理のため長く設定。"),
        ("Java / JDBC", "MySQL Connector/J", "autoReconnect", "再接続制御", "Boolean", "false", "false (維持)", "false (維持)", "プールと競合するため無効", "接続プロパティ", "trueにするとトランザクション状態やセッション変数が初期化されてデータ不整合の原因となるため、絶対にfalseを維持。"),

        # RDS Proxy
        ("DB Proxy", "Amazon RDS Proxy", "idle_client_timeout", "接続維持(L7)", "秒", "1800 秒 (30分)", "1800 秒 (30分)", "1800〜28800 秒 (※直接接続推奨)", "App Pool Idle (10分) < Proxy < DB wait", "RDS Proxy 設定 (idle-client-timeout)", "【黄金律】クライアントからの無通信コネクションを閉じる時間。JBoss(10分)より長く、MySQL(8時間)より短く設定することで完全整合。"),
        ("DB Proxy", "Amazon RDS Proxy", "connection_borrow_timeout", "借用待機", "秒", "120 秒", "10 秒", "60 秒 (※直接接続推奨)", "Borrow Timeout < API GW (29s)", "RDS Proxy ターゲットグループ属性", "Auroraへのバックエンド接続が満杯の時の待ち時間。デフォルト120秒はオンラインでは論外(API GWが29秒で切断)。10秒で即座にエラーを返却。"),
        ("DB Proxy", "Amazon RDS Proxy", "max_connections_percent", "プール上限", "%", "100 %", "90 %", "N/A", "DB max_connections の90%", "RDS Proxy ターゲットグループ属性", "Aurora全体のmax_connectionsに対するProxy利用上限。残り10%を管理操作やバッチ直接接続、緊急メンテ用に確保。"),
        ("DB Proxy", "Amazon RDS Proxy", "max_idle_connections_percent", "接続維持", "%", "50 %", "50 %", "N/A", "ウォーム接続維持", "RDS Proxy ターゲットグループ属性", "プロキシがAuroraとの間でアイドル状態のままキープするコネクション割合。スパイク時の接続オーバーヘッドを低減。"),

        # Aurora Serverless v2 (MySQL 8.4.7 LTS)
        ("Database", "Aurora MySQL 8.4.7", "wait_timeout", "接続維持(L7)", "秒", "28800 秒 (8時間)", "28800 秒 (デフォルト維持)", "28800 秒", "DB wait_timeout > Proxy Idle (30分)", "DB パラメータグループ", "【黄金律】非対話型接続の無通信切断時間。RDS Proxy(30分)より遥かに長いため、DB側から不意にセッションが切断される事故を完全に防止。"),
        ("Database", "Aurora MySQL 8.4.7", "interactive_timeout", "接続維持(L7)", "秒", "28800 秒 (8時間)", "28800 秒 (デフォルト維持)", "28800 秒", "DB > Proxy", "DB パラメータグループ", "対話型接続の無通信切断時間。"),
        ("Database", "Aurora MySQL 8.4.7", "net_read_timeout", "パケット待機", "秒", "30 秒", "30 秒 (デフォルト維持)", "60 秒", "net_read_timeout > 瞬断検知", "DB パラメータグループ", "クライアントからの次のデータパケット着信待機時間。"),
        ("Database", "Aurora MySQL 8.4.7", "net_write_timeout", "パケット待機", "秒", "60 秒", "60 秒 (デフォルト維持)", "120 秒", "net_write_timeout > 送信バッファ", "DB パラメータグループ", "クライアントへのレスポンス送信ブロック待機時間。大量レコード返却時の中断を防止。"),
        ("Database", "Aurora MySQL 8.4.7", "connect_timeout", "接続確立", "秒", "10 秒", "10 秒 (デフォルト維持)", "10 秒", "ハンドシェイク完了制限", "DB パラメータグループ", "mysqldが接続パケットに応答するまでの待機時間。Bad handshake攻撃防止。"),
        ("Database", "Aurora MySQL 8.4.7", "innodb_lock_wait_timeout", "行ロック競合", "秒", "50 秒", "15 秒", "50 秒 (または個別指定)", "Lock Wait < API GW (29s)", "DB パラメータグループ / セッション", "行ロック獲得待ち上限。オンラインでデフォルト50秒待つとAPI GW(29s)で確実に死ぬ。15秒で即座にエラー(Error 1205)を起こしてロールバック。"),
        ("Database", "Aurora MySQL 8.4.7", "lock_wait_timeout", "メタデータロック", "秒", "31536000 秒 (1年)", "60 秒", "300 秒", "DDL/メタデータロック待機", "DB パラメータグループ", "テーブル構造変更(DDL)やテーブルロック時の待機上限。1年は長すぎるため、オンライン停止を防ぐため60秒に短縮。"),
        ("Database", "Aurora MySQL 8.4.7", "max_execution_time", "クエリ実行監視", "ミリ秒", "0 (無制限)", "15000 (15秒)", "0 (無制限 / バッチ完走)", "DB Execution < JDBC Socket (20s)", "DB パラメータグループ / セッション", "【ゾンビクエリ殺害】SELECT文の最大実行時間。15秒でMySQL自身がクエリを中断(Error 3024)。ACUの急騰とリソース浪費を根絶。")
    ]
    
    start_row_m = 5
    for row_idx, r_data in enumerate(master_rows, start_row_m):
        is_zebra = (row_idx % 2 == 0)
        for col_idx, val in enumerate(r_data, 1):
            cell = ws2.cell(row=row_idx, column=col_idx, value=val)
            cell.font = font_data_bold if col_idx in [2, 3, 7, 8] else font_data
            cell.fill = fill_zebra if is_zebra else fill_white
            cell.border = border_cell
            
            # Alignments
            if col_idx in [1, 4, 5]:
                cell.alignment = align_center
            elif col_idx in [6, 7, 8]:
                cell.alignment = align_center
            else:
                cell.alignment = align_left
        ws2.row_dimensions[row_idx].height = 42

    # =========================================================================
    # SHEET 3: 3_オンラインvsバッチ比較 (Online vs Batch In-depth Comparison)
    # =========================================================================
    ws3 = wb.create_sheet(title="3_オンラインvsバッチ比較")
    ws3.views.sheetView[0].showGridLines = True
    
    ws3["A1"] = "オンライン処理 vs バッチ処理のタイムアウト設計・接続差異"
    ws3["A1"].font = font_title
    ws3["A2"] = "JBoss EAP 8.1 JNDI接続 vs Java standalone Connector/J 直接実行の徹底比較"
    ws3["A2"].font = font_subtitle
    
    ws3.row_dimensions[1].height = 28
    ws3.row_dimensions[2].height = 20
    ws3.row_dimensions[4].height = 28
    
    headers_comp = [
        "比較項目",
        "オンライン処理 (JBoss EAP 8.1 / ECS Fargate)",
        "バッチ処理 (Java Standalone / EC2)",
        "アーキテクチャ上の理由・背景",
        "推奨設定・実装コード例"
    ]
    for col_idx, h in enumerate(headers_comp, 1):
        cell = ws3.cell(row=4, column=col_idx, value=h)
        cell.font = font_tbl_header
        cell.fill = fill_tbl_header
        cell.alignment = align_header
        cell.border = border_header
        
    comp_rows = [
        ("実行形態・コンテナ環境",
         "ECS Fargate タスク上で常駐する JBoss EAP 8.1 (Jakarta EE 10)。Web APIとしてHTTPリクエストを並行処理。",
         "EC2 上で cron / 運用ジョブスケジューラから起動される java コマンド。オンラインと同じクラスファイル・資材を -cp でロード。",
         "オンラインはマルチスレッドで大量の短時間トランザクションをさばく。バッチは単一または制御されたスレッドで大量データを逐次/バルク処理。",
         "オンライン: ECSタスク定義 (メモリ/CPU割り当て)\nバッチ: java -Xms4g -Xmx4g -cp \"app.jar:lib/*\" com.example.BatchMain"),
         
        ("DB接続方式とデータソース取得",
         "JBoss EAP 内部の JNDI (java:jboss/datasources/MySqlDS) 経由。\nIronJacamar JCA コネクションプールが完全管理。",
         "JNDIはAPコンテナ外のため利用不可。\nConnector/J DriverManager / DataSource をJavaコード内で直接生成 (または軽量HikariCP)。",
         "オンラインはコンテナ管理DataSource。バッチはスタンドアロンのため、設定はプロパティファイルまたは環境変数から取得してJDBC URLに注入する。",
         "オンライン: JNDI lookup (\"java:comp/env/jdbc/mydb\")\nバッチ: DriverManager.getConnection(jdbcUrl, props)"),
         
        ("socketTimeout の指定場所と値",
         "【指定場所】standalone.xml の <datasource> 内\n<connection-property name=\"socketTimeout\">20000</connection-property>\n【推奨値】20000 ms (20秒)",
         "【指定場所】バッチ設定ファイル / JDBC接続URL\njdbc:mysql://...?socketTimeout=600000\n【推奨値】600000 ms (10分) または 0 (無制限/個別Statement指定)",
         "オンラインはAPI Gateway(29秒)の制約があるため20秒で強制切断して保護。\nバッチは1クエリに数分要する集計・一括更新があるため、20秒にすると途中で全滅する。",
         "オンライン: socketTimeout=20000\nバッチ: socketTimeout=600000 (バッチSLOに合わせて設定)"),
         
        ("connectTimeout の指定場所と値",
         "【指定場所】standalone.xml の <connection-property name=\"connectTimeout\">5000</connection-property>\n【推奨値】5000 ms (5秒)",
         "【指定場所】JDBC接続URL / プロパティ\nconnectTimeout=10000\n【推奨値】10000 ms (10秒)",
         "接続確立は素早く行うべきだが、バッチは夜間等にネットワーク負荷やDBフェイルオーバーが発生しても少し粘れるよう10秒程度許容。",
         "オンライン: 5000 ms\nバッチ: 10000 ms"),
         
        ("クエリタイムアウト制御 (SQL実行制限)",
         "【JBoss側で一括制御】\n<query-timeout>20</query-timeout>\n<set-tx-query-timeout>true</set-tx-query-timeout>\nAurora側: max_execution_time=15000 (15秒)",
         "【Javaコード側で個別制御】\nStatement.setQueryTimeout(秒数)\nAurora側: バッチ接続セッションは max_execution_time=0 (無制限)",
         "オンラインは全クエリを短時間で終えることが絶対条件。バッチは処理内容に応じて「30秒のクエリ」も「10分のクエリ」も存在するため、共通一律制限ではなくSQLごとに設定。",
         "オンライン: JBoss設定で自動適用\nバッチ: ps.setQueryTimeout(600); // 10分"),
         
        ("トランザクションタイムアウト",
         "【JTA グローバルトランザクション】\n<coordinator-environment default-timeout=\"25\"/>\n25秒で強制ロールバック。",
         "【ローカルJDBCトランザクション】\n自動コミットOFF (connection.setAutoCommit(false)) で業務単位ごとにcommit()。必要に応じてジョブ全体タイマー監視。",
         "オンラインはリクエストごとにJTA境界。バッチは1000件コミットなどのチャンク処理を行うため、長時間のトランザクションを業務要件に合わせて制御する。",
         "オンライン: default-timeout=\"25\"\nバッチ: チャンク単位のコミットとリトライ制御"),
         
        ("【超重要】RDS Proxy 経由の是非とピニング問題",
         "【RDS Proxy 経由: 必須・最適】\nLambda/ECSからの突発的な接続急増を吸収し、フェイルオーバーを高速化。",
         "【RDS Proxy 経由: 原則非推奨・直接接続を強く推奨】\nAuroraのWriter/Readerクラスタエンドポイントに直接接続することがAWSのベストプラクティス！",
         "バッチがRDS Proxyを経由すると、\n① 長時間トランザクションにより「ピニング(Pinning)」が発生し、Proxyの接続を占有してしまう。\n② バッチがProxy接続を枯渇させ、オンライン側のAPIが全滅する。\n③ Proxyのidle_client_timeout(30分)でバッチが切断される。",
         "バッチの接続先URL:\njdbc:mysql://aurora-cluster.cluster-xxxx.rds.amazonaws.com:3306/mydb\n(RDS ProxyのエンドポイントではなくAuroraクラスタエンドポイントを指定)")
    ]
    
    start_row_c = 5
    for row_idx, r_data in enumerate(comp_rows, start_row_c):
        is_zebra = (row_idx % 2 == 0)
        for col_idx, val in enumerate(r_data, 1):
            cell = ws3.cell(row=row_idx, column=col_idx, value=val)
            cell.font = font_data_bold if col_idx in [1, 4] else font_data
            cell.fill = fill_zebra if is_zebra else fill_white
            cell.border = border_cell
            cell.alignment = align_left
        ws3.row_dimensions[row_idx].height = 68

    # =========================================================================
    # SHEET 4: 4_小学生でもわかる解説 (Kid-friendly Metaphors & History)
    # =========================================================================
    ws4 = wb.create_sheet(title="4_小学生でもわかる解説")
    ws4.views.sheetView[0].showGridLines = True
    
    ws4["A1"] = "小学生でも絶対にわかる！タイムアウトの仕組み・歴史・登場の背景"
    ws4["A1"].font = font_title
    ws4["A2"] = "難しい専門用語ゼロ！「超高級レストランの伝言ゲーム」と「電話の保留」で完全理解"
    ws4["A2"].font = font_subtitle
    
    ws4.row_dimensions[1].height = 28
    ws4.row_dimensions[2].height = 20
    ws4.row_dimensions[4].height = 26
    
    # Story 1
    ws4.merge_cells("A4:F4")
    c = ws4.cell(row=4, column=1, value="第1章: キャラクター紹介（レストランの登場人物たち）")
    c.font = font_sec_header
    c.fill = fill_sec_dark
    c.alignment = align_left
    
    char_data = [
        ("お客さん（クライアントブラウザ）", "お腹を空かせて料理を注文しに来た人。「早く料理を出して！」と待っています。"),
        ("受付のせっかち店長（API Gateway）", "お店のルールに超厳しい受付。「29秒以内に料理が出ないなら、お客さんを帰らせる！」とストップウォッチを持っています。"),
        ("ホールの給仕係（ALB）", "注文票を受け取って厨房へ届ける係。厨房が返事をくれないと困ってしまいます。"),
        ("料理長（ECS Fargate / JBoss EAP）", "レシピ（Javaプログラム）を見て料理を作る責任者。食材を冷蔵庫から取ってくるよう指示します。"),
        ("冷蔵庫マネージャー（RDS Proxy）", "食材の出し入れを整理する係。コンロや冷蔵庫の数が限られているので、順番をテキパキ管理します。"),
        ("頑固な鉄人シェフ（Aurora MySQL）", "一番奥でじっくり食材（データ）を加工するシェフ。注文が重いとずっとフライパンを振り続けます。")
    ]
    curr_row_s = 5
    for name, desc in char_data:
        ws4.cell(row=curr_row_s, column=1, value=name).font = font_data_bold
        ws4.cell(row=curr_row_s, column=1).fill = fill_sub_header
        ws4.cell(row=curr_row_s, column=1).border = border_cell
        ws4.cell(row=curr_row_s, column=1).alignment = align_left
        
        ws4.merge_cells(start_row=curr_row_s, start_column=2, end_row=curr_row_s, end_column=6)
        c = ws4.cell(row=curr_row_s, column=2, value=desc)
        c.font = font_data
        c.fill = fill_white
        c.border = border_cell
        c.alignment = align_left
        ws4.row_dimensions[curr_row_s].height = 26
        curr_row_s += 1
        
    curr_row_s += 1
    # Story 2
    ws4.merge_cells(start_row=curr_row_s, start_column=1, end_row=curr_row_s, end_column=6)
    c = ws4.cell(row=curr_row_s, column=1, value="第2章: なぜ「client timeout < proxy timeout < database_timeout」なの？（電話の保留チキンレース）")
    c.font = font_sec_header
    c.fill = fill_sec_dark
    c.alignment = align_left
    ws4.row_dimensions[curr_row_s].height = 26
    curr_row_s += 1
    
    story_idle = (
        "【ある日のおバカな事件】\n"
        "料理長（JBoss）と、冷蔵庫マネージャー（RDS Proxy）と、頑固シェフ（Aurora）は、内線電話をつなぎっぱなしにしていました。\n"
        "しばらくお客さんが来なかったので、沈黙が続きました。\n\n"
        "30分経ったとき、冷蔵庫マネージャー（Proxy）が勝手に思いました。\n"
        "「誰も喋らないから、勝手にガチャリと電話を切っちゃおう！（Proxyタイムアウト）」\n"
        "でも、料理長（JBoss）は電話が切られたことを知りません。「まだ繋がってるぞ」と思っています。\n\n"
        "その直後、新しいお客さんがやってきました！料理長は受話器に向かって「もしもし！ハンバーグちょうだい！」と叫びました。\n"
        "しかし受話器からは「ツーツーツー……（切断音）」。\n"
        "料理長は大パニック！「ギャー！電話が切れてる！料理が出せない！」とお客さんに大失敗のエラーを出してしまいました。\n"
        "これがエンジニアが恐れる『Communications link failure（通信リンク障害）』です！\n\n"
        "【解決策：お行儀の良いルール】\n"
        "「電話をかけている料理長（クライアント）が、10分誰も喋らなかったら『自分から綺麗にお電話を切って、次話すときにかけ直す』ようにしよう！」\n"
        "料理長（10分） < 冷蔵庫マネージャー（30分） < 頑固シェフ（8時間）の順番にすれば、相手から勝手に切られる事故は絶対に起きません！"
    )
    ws4.merge_cells(start_row=curr_row_s, start_column=1, end_row=curr_row_s, end_column=6)
    c = ws4.cell(row=curr_row_s, column=1, value=story_idle)
    c.font = font_data
    c.fill = fill_callout
    c.border = border_cell
    c.alignment = align_left
    ws4.row_dimensions[curr_row_s].height = 160
    curr_row_s += 2
    
    # Story 3
    ws4.merge_cells(start_row=curr_row_s, start_column=1, end_row=curr_row_s, end_column=6)
    c = ws4.cell(row=curr_row_s, column=1, value="第3章: 処理待ちタイムアウトの悲劇（せっかち店長とゾンビシェフ）")
    c.font = font_sec_header
    c.fill = fill_sec_dark
    c.alignment = align_left
    ws4.row_dimensions[curr_row_s].height = 26
    curr_row_s += 1
    
    story_exec = (
        "【せっかち店長の29秒ルール】\n"
        "受付の店長（API Gateway）は、お客さんを29秒以上絶対に待たせません。29秒経つと「時間切れ！お帰りください！」と追い出します（504エラー）。\n\n"
        "もし、奥の頑固シェフ（Aurora）が「オレは納得いくまで60秒じっくり煮込むぞ」と料理を続けていたらどうなるでしょう？\n"
        "店長はお客さんをもう追い出したのに、シェフは誰もいない客のためにガスコンロをガンガン燃やし、フライパンを独占し続けています！\n"
        "これを見た次の客は、フライパンが空かないので料理が作ってもらえず、お店全体が大渋滞（カスケード障害）になります！\n"
        "この無駄に動き続けるシェフを『ゾンビクエリ』と呼びます。クラウドの電気代（Aurora ACU）も爆発します！\n\n"
        "【解決策：奥から早くあきらめる】\n"
        "シェフが15秒で「これ以上時間かかるなら無理！」とあきらめ、料理長が20秒で「申し訳ありません」と準備し、\n"
        "店長が29秒で追い出す前に、お客さんに「申し訳ありません、混雑しています」と丁寧なお手紙（JSONエラー）を渡すのがプロの仕事です！"
    )
    ws4.merge_cells(start_row=curr_row_s, start_column=1, end_row=curr_row_s, end_column=6)
    c = ws4.cell(row=curr_row_s, column=1, value=story_exec)
    c.font = font_data
    c.fill = fill_zebra
    c.border = border_cell
    c.alignment = align_left
    ws4.row_dimensions[curr_row_s].height = 155
    curr_row_s += 2

    # History
    ws4.merge_cells(start_row=curr_row_s, start_column=1, end_row=curr_row_s, end_column=6)
    c = ws4.cell(row=curr_row_s, column=1, value="第4章: 歴史と背景 〜なぜ昔は問題にならず、クラウドで必須になったのか？〜")
    c.font = font_sec_header
    c.fill = fill_sec_dark
    c.alignment = align_left
    ws4.row_dimensions[curr_row_s].height = 26
    curr_row_s += 1
    
    story_history = (
        "【昔（オンプレミス・モノリス時代）】\n"
        "昔のシステムは、社内LAN（1本の太い線）で「パソコン → APサーバ → 単一データベース」が直結されていました。\n"
        "中間に邪魔をする機械がなく、ネットワークも切れないため、タイムアウトを『0（無制限）』にしておいても平和に動いていました。\n\n"
        "【現代（クラウド・マイクロサービス時代）】\n"
        "クラウドになり、セキュリティを高めるため、間に「API Gateway」「ファイアウォール(Palo Alto)」「ロードバランサ(ALB)」「DBプロキシ(RDS Proxy)」と、\n"
        "たくさんの『中継係（プロキシ）』が挟まるようになりました。\n"
        "これらの中継係は、自分たちのメモリを守るために『通信がない接続は勝手に切断するタイマー』を各自勝手に持っています。\n"
        "その結果、制限時間の順番がバラバラだと、途中の誰かが勝手に回線を切ってシステム全体が壊れるようになりました。\n"
        "そのため、クラウド時代にはすべてのレイヤーの時間をミリ秒単位で揃える『タイムアウト階層設計』が必須技術になったのです！"
    )
    ws4.merge_cells(start_row=curr_row_s, start_column=1, end_row=curr_row_s, end_column=6)
    c = ws4.cell(row=curr_row_s, column=1, value=story_history)
    c.font = font_data
    c.fill = fill_callout
    c.border = border_cell
    c.alignment = align_left
    ws4.row_dimensions[curr_row_s].height = 145

    # =========================================================================
    # SHEET 5: 5_障害パターンと設定根拠 (Failure Modes & Engineering Scenarios)
    # =========================================================================
    ws5 = wb.create_sheet(title="5_障害パターンと設定根拠")
    ws5.views.sheetView[0].showGridLines = True
    
    ws5["A1"] = "タイムアウト不整合による代表的障害パターンと設計根拠"
    ws5["A1"].font = font_title
    ws5["A2"] = "実運用のトラブルシューティングと防止設計のメカニズム"
    ws5["A2"].font = font_subtitle
    
    ws5.row_dimensions[1].height = 28
    ws5.row_dimensions[2].height = 20
    ws5.row_dimensions[4].height = 28
    
    headers_fail = [
        "障害パターン / 現象名",
        "発生メカニズム (何が起きるか)",
        "引き起こされるエラーログ / コード",
        "根本原因となる設定不備",
        "恒久対策・設定方針"
    ]
    for col_idx, h in enumerate(headers_fail, 1):
        cell = ws5.cell(row=4, column=col_idx, value=h)
        cell.font = font_tbl_header
        cell.fill = fill_tbl_header
        cell.alignment = align_header
        cell.border = border_header
        
    fail_rows = [
        ("サイレント切断障害\n(Communications Link Failure)",
         "JBossのコネクションプールが保持するコネクションに対し、RDS Proxy(30分)またはAurora(8時間)が先にアイドルタイムアウトを切断。JBossが次のクエリでこの死んだコネクションを使い、TCP RSTを受信して爆死する。",
         "java.sql.SQLException: Communications link failure\nLast packet sent successfully to server was ...\nConnection reset by peer",
         "JBossのidle-timeout-minutes (例: 60分) が RDS Proxyのidle_client_timeout (30分) より長い。\nまたはテストクエリ(validation)が無効。",
         "【黄金律の適用】\nJBoss idle-timeout-minutes (10分) < RDS Proxy idle_client_timeout (30分) に設定。\nbackground-validation-millis=60000 を設定。"),
         
        ("ゾンビクエリとリソース枯渇\n(Orphan Query & Cascade Failure)",
         "API Gatewayが29秒で504を返してクライアントを切断したが、ECS JBossとAurora側でクエリが動き続け、行ロックを抱え込んだままACUが急上昇。後続リクエストがロック待ちで連鎖的に全滅する。",
         "HTTP 504 Gateway Timeout (CloudWatch)\nAurora Serverless v2 ACU急騰\nInnoDB Lock Wait Timeout (1205)",
         "JDBC socketTimeout=0 (無制限) または > 29秒。\nAurora max_execution_time=0 (無制限)。\ninnodb_lock_wait_timeout=50秒 (API GWより長い)。",
         "【フェイルファスト階層化】\nAurora max_execution_time=15000 (15秒)\ninnodb_lock_wait_timeout=15秒\nJBoss JTA default-timeout=25秒\nJDBC socketTimeout=20000 (20秒)"),
         
        ("ALB-ECS間のレースコンディション\n(突発的 502 Bad Gateway)",
         "ALBのIdle Timeout(60秒)とECS JBoss(Undertow)のKeep-Alive(60秒)が同一値の場合、JBossが「60秒経ったから切る(TCP FIN)」としたまさにその瞬間に、ALBが新しいHTTPリクエストを流し込み、接続リセットが発生する。",
         "HTTP 502 Bad Gateway (ALBメトリクス HTTPCode_ELB_502_Count)\nCloudWatch ALBアクセスログ elb_status_code=502",
         "ALB Idle Timeout == JBoss Undertow keep-alive-timeout (同値競合)\nまたは JBoss側のKeep-AliveがALBより短い。",
         "【上流 < 下流 の徹底】\nALB Idle Timeout = 60秒 に対し、\nJBoss Undertow keep-alive-timeout = 65000ms (65秒) と、バックエンド側を必ず長く設定。"),
         
        ("バッチによるRDS Proxyピニング枯渇\n(オンライン全滅障害)",
         "バッチ処理がRDS Proxyを経由して大量のPrepared Statementや長時間トランザクションを実行したため、RDS ProxyのDB接続がすべてバッチにピン留め(Pinning)され、オンライン用の接続プールが枯渇する。",
         "RDS Proxy: DatabaseConnectionsBorrowLatency急上昇\nClient error: Cannot get a connection from the pool within 120 seconds",
         "バッチ処理がオンラインと同じRDS Proxyエンドポイントを共有している。\nPrepared Statementキャッシュや一時テーブル利用によるピニング。",
         "【接続経路の完全分離】\nバッチはRDS Proxyを経由せず、Auroraクラスタエンドポイント(Writer/Reader)に直接接続する。\nオンライン側RDS Proxyのmax_connections_percent=90%として管理枠を確保。"),
         
        ("コネクションプール借用死\n(Blocking Timeout Exhaustion)",
         "高負荷時にJBossのプール接続がすべて使用中になり、新規リクエストが接続待ち行列に入る。デフォルトで30秒待つため、API Gatewayの29秒制限を超えてしまい、すべて504エラーとなって全スレッドが詰まる。",
         "javax.resource.ResourceException: IJ000453: Unable to get managed connection for ...\nAPI Gateway 504 Gateway Timeout",
         "JBoss blocking-timeout-millis = 30000ms (30秒) が API Gatewayの29秒制限を超えている。",
         "【即時フェイルファスト】\nblocking-timeout-millis = 5000ms (5秒) に短縮。\nプールが枯渇した際は5秒で即座にエラーを返し、API GWのタイムアウトによるスレッド滞留を防ぐ。")
    ]
    
    start_row_f = 5
    for row_idx, r_data in enumerate(fail_rows, start_row_f):
        is_zebra = (row_idx % 2 == 0)
        for col_idx, val in enumerate(r_data, 1):
            cell = ws5.cell(row=row_idx, column=col_idx, value=val)
            cell.font = font_data_bold if col_idx in [1, 3] else font_data
            cell.fill = fill_zebra if is_zebra else fill_white
            cell.border = border_cell
            cell.alignment = align_left
        ws5.row_dimensions[row_idx].height = 68

    # =========================================================================
    # Auto-adjust column widths across all sheets
    # =========================================================================
    col_width_rules = {
        "1_全体設計原則と黄金律": {1: 6, 2: 24, 3: 16, 4: 26, 5: 32, 6: 32, 7: 42},
        "2_タイムアウト推奨値一覧": {1: 15, 2: 26, 3: 28, 4: 15, 5: 8, 6: 22, 7: 24, 8: 24, 9: 28, 10: 32, 11: 48},
        "3_オンラインvsバッチ比較": {1: 24, 2: 36, 3: 36, 4: 38, 5: 42},
        "4_小学生でもわかる解説": {1: 28, 2: 22, 3: 22, 4: 22, 5: 22, 6: 26},
        "5_障害パターンと設定根拠": {1: 26, 2: 38, 3: 36, 4: 36, 5: 38}
    }
    
    for ws in wb.worksheets:
        rules = col_width_rules.get(ws.title, {})
        for col_idx in range(1, ws.max_column + 1):
            col_letter = get_column_letter(col_idx)
            if col_idx in rules:
                ws.column_dimensions[col_letter].width = rules[col_idx]
            else:
                ws.column_dimensions[col_letter].width = 20
                
    # Freeze Panes
    ws1.freeze_panes = "A5"
    ws2.freeze_panes = "A5"
    ws3.freeze_panes = "A5"
    ws4.freeze_panes = "A5"
    ws5.freeze_panes = "A5"

    wb.save(filename)
    print(f"Successfully generated {filename}")

if __name__ == "__main__":
    create_timeout_workbook()

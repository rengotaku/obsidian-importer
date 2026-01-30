---
title: OpenMediaVaultの共有フォルダへのアクセス方法
normalized: true
created: 2025-11-19
tags:
  - claude-export
  - conversation
uuid: 568f77f0-99d4-454d-97da-7f09bd1cd257
updated: 2025-11-20
message_count: 28
---
# OpenMediaVaultの共有フォルダへのアクセス方法

## Summary

**Conversation Overview**

The user sought help configuring and troubleshooting OpenMediaVault (OMV), a network-attached storage system running on a Raspberry Pi. They initially needed guidance on accessing shared folders from Ubuntu, with OMV configured to share folders via both SMB/CIFS and NFS protocols. Claude provided comprehensive instructions for mounting NFS shares from Ubuntu, including both GUI and command-line methods, plus automatic mounting via /etc/fstab.

The conversation then shifted to troubleshooting OMV's rsync synchronization feature. The user discovered that while manual rsync execution worked perfectly (successfully syncing 195MB from a ~909TB source), the scheduled automatic execution wasn't occurring. Through systematic troubleshooting, they determined that the cron service was running properly and the rsync job was correctly registered, but the schedule was set to execute only on specific days of each month (1st, 10th, 20th, and 21st at 3:10 AM) rather than daily. The user had expected more frequent execution.

Claude helped analyze the cron configuration files, particularly /etc/cron.d/nas-server-rsync, and explained how to interpret the cron schedule format. They also addressed mail notification issues, initially thinking the mail system wasn't configured, but the user clarified that OMV's notification system was properly set up and they had received emails from manual executions. The user showed interest in a script to monitor file modification times and count files by date ranges for tracking synchronization activity. Claude provided several script variations for analyzing file timestamps and generating reports. The conversation concluded with the user asking about two uninstalled OMV plugins (anacron and wakealarm), which Claude confirmed would not affect the current cron functionality since their server runs continuously.

## Conversation

### 👤 Human (2025-11-19 22:18)

nas-serverで、
ストレージ-共有フォルダ
で設定しているのだけど、どのようにアクセスすれば？

### 🤖 Assistant (2025-11-19 22:18)

 OpenMediaVaultの共有フォルダへのアクセス方法は、設定したプロトコルによって異なります。一般的な方法を説明します。

## SMB/CIFS（Windows共有）の場合

**macOSから:**
1. Finderを開く
2. メニューバーから「移動」→「サーバへ接続」（Command + K）
3. `smb://サーバーのIPアドレス/共有フォルダ名` を入力
   - 例: `smb://192.168.1.100/共有フォルダ`
4. ユーザー名とパスワードを入力

**Windowsから:**
1. エクスプローラーを開く
2. アドレスバーに `\\サーバーのIPアドレス\共有フォルダ名` を入力
   - 例: `\\192.168.1.100\共有フォルダ`
3. ユーザー名とパスワードを入力

## NFS（Unix/Linux共有）の場合

**LinuxやmacOSから:**
```bash
sudo mount -t nfs サーバーのIPアドレス:/共有パス /マウントポイント
```

## 確認すべき設定

OpenMediaVaultで以下を確認してください:
1. **サービス** → **SMB/CIFS** または **NFS** が有効になっているか
2. 共有フォルダに対して、該当サービスの共有設定がされているか
3. アクセス権限（ユーザー/グループ）が正しく設定されているか

どのプロトコルで設定されているか、またはどのOSからアクセスしたいか教えていただければ、より具体的にご案内できます。

### 👤 Human (2025-11-19 22:20)

ubuntuからは？

### 🤖 Assistant (2025-11-19 22:20)

 Ubuntuからは以下の方法でアクセスできます。

## GUIでアクセス（ファイルマネージャー使用）

**Nautilus（Ubuntuデフォルトのファイルマネージャー）:**
1. ファイルマネージャーを開く
2. 左サイドバーの「他の場所」をクリック
3. 下部の「サーバーへ接続」に以下を入力:
   - SMBの場合: `smb://サーバーのIPアドレス/共有フォルダ名`
   - NFSの場合: `nfs://サーバーのIPアドレス/共有パス`
4. 「接続」をクリックしてユーザー名・パスワードを入力

## コマンドラインでマウント

**SMB/CIFSの場合:**
```bash
# cifs-utilsをインストール（未インストールの場合）
sudo apt install cifs-utils

# 一時的にマウント
sudo mkdir -p /mnt/omv
sudo mount -t cifs //サーバーのIPアドレス/共有フォルダ名 /mnt/omv -o username=ユーザー名,password=パスワード

# または対話的にパスワード入力
sudo mount -t cifs //サーバーのIPアドレス/共有フォルダ名 /mnt/omv -o username=ユーザー名
```

**NFSの場合:**
```bash
# nfs-commonをインストール（未インストールの場合）
sudo apt install nfs-common

# マウント
sudo mkdir -p /mnt/omv
sudo mount -t nfs サーバーのIPアドレス:/共有パス /mnt/omv
```

## 起動時に自動マウント（/etc/fstab）

**SMBの場合:**
```bash
# 認証情報ファイルを作成
sudo nano /root/.credentials
```
内容:
```
username=ユーザー名
password=パスワード
```
```bash
sudo chmod 600 /root/.credentials

# /etc/fstabに追加
sudo nano /etc/fstab
```
追加する行:
```
//サーバーのIPアドレス/共有フォルダ名 /mnt/omv cifs credentials=/root/.credentials,iocharset=utf8 0 0
```

**NFSの場合:**
```bash
sudo nano /etc/fstab
```
追加する行:
```
サーバーのIPアドレス:/共有パス /mnt/omv nfs defaults 0 0
```

設定後:
```bash
sudo mount -a  # 全てのfstabエントリをマウント
```

OpenMediaVaultでSMBとNFSのどちらを有効にしているか教えていただければ、より具体的にサポートできます。

### 👤 Human (2025-11-19 22:22)

File access control lists　に下記のように出ているが。どうすれば？


名前
タイプ
システムアカウント
パーミッション
pi
User
pi
Group
webdav-users
Group
_apt
User
_chrony
User
107 合計
* 
* 
* 1
* 2
* 3
* 4
* 5
* 
* 
ユーザー/グループのパーミッション

### 🤖 Assistant (2025-11-19 22:23)

 これはOpenMediaVaultの共有フォルダのACL（アクセス制御リスト）設定画面ですね。共有フォルダにアクセスするには、ユーザーやグループに適切なパーミッションを設定する必要があります。

## 設定手順

1. **ユーザー/グループを追加**
   - 画面上部の「**+**」ボタンをクリック
   - アクセスを許可したいユーザーまたはグループを選択
   - パーミッションを設定:
     - **読み取り/書き込み**: フルアクセス（推奨）
     - **読み取り専用**: 読み込みのみ
     - **書き込み専用**: 書き込みのみ（稀）

2. **既存のパーミッションを変更**
   - リストから該当のユーザー/グループを選択
   - 鉛筆アイコン（編集ボタン）をクリック
   - パーミッションを変更して保存

3. **保存して適用**
   - 設定後、画面上部の「保存」ボタンをクリック
   - 黄色い通知バーが表示されたら「適用」をクリック

## 推奨設定

Ubuntuからアクセスする場合:

1. **OpenMediaVaultでユーザーを作成済み**の場合:
   - そのユーザーを追加して「読み取り/書き込み」権限を付与

2. **新しくユーザーを作成**する場合:
   - 「ユーザー」→「ユーザー」から新規ユーザーを作成
   - ACL設定でそのユーザーを追加

3. **グループでの管理**（複数ユーザーがいる場合）:
   - 「ユーザー」→「グループ」で新規グループ作成
   - ユーザーをそのグループに所属させる
   - ACL設定でグループに権限を付与

現在どのユーザーでアクセスしたいか教えていただければ、より具体的な設定をご案内できます。

### 👤 Human (2025-11-19 22:24)

Ubuntuの利用ユーザは、
ubuntu:~/Workspace$ id
uid=1000(takuya) gid=1000(takuya) groups=1000(takuya),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev),100(users),109(kvm),122(lpadmin),135(lxd),136(sambashare),142(libvirt),999(ollama),1001(devuser)

だけど、どのようなユーザ作成した？

### 🤖 Assistant (2025-11-19 22:24)

 OpenMediaVaultで作成したユーザーを確認しましょう。

## OpenMediaVaultでユーザーを確認

1. OpenMediaVaultの管理画面にログイン
2. 左メニューから「**ユーザー**」→「**ユーザー**」を開く
3. 作成済みのユーザー一覧が表示されます

## 推奨される設定方法

Ubuntuの`takuya`ユーザーでアクセスする場合、以下の2つの方法があります:

### 方法1: OpenMediaVaultで`takuya`ユーザーを作成（推奨）

1. 「ユーザー」→「ユーザー」→「**+**」（追加）
2. 以下を設定:
   - **名前**: `takuya`
   - **パスワード**: 任意のパスワード（Ubuntuと同じでもOK）
   - **UID**: `1000`（重要: Ubuntuと同じUIDにする）
   - **グループ**: `users`または新規作成
3. 保存

### 方法2: 既存のOpenMediaVaultユーザーを使用

既にOpenMediaVaultでユーザーを作成している場合は、そのユーザー名とパスワードを使ってアクセスできます。

## ACL設定に戻る

ユーザーを確認・作成したら:
1. 「ストレージ」→「共有フォルダ」→該当のフォルダを選択
2. 「権限」タブ→「**+**」
3. 作成した`takuya`ユーザー（またはグループ`users`）を追加
4. パーミッション: **読み取り/書き込み**を選択
5. 保存→適用

OpenMediaVaultで現在どのようなユーザーが作成されているか教えていただけますか？

### 👤 Human (2025-11-19 22:29)

NFSで共有している

共有フォルダ
クライアント
オプション
Tags
ShareFiles
10.0.0.0/24
insecure, rw, subtree_check

### 🤖 Assistant (2025-11-19 22:30)

 NFSで共有されているのであれば、設定は既にできていますね。UbuntuからNFSマウントする方法を説明します。

## NFSでマウントする手順

### 1. nfs-commonのインストール（未インストールの場合）
```bash
sudo apt update
sudo apt install nfs-common
```

### 2. マウントポイントを作成
```bash
sudo mkdir -p /mnt/ShareFiles
# または好きな場所に
# mkdir -p ~/mnt/ShareFiles
```

### 3. NFSマウント
```bash
# OpenMediaVaultのIPアドレスを確認してから実行
sudo mount -t nfs OpenMediaVaultのIPアドレス:/export/ShareFiles /mnt/ShareFiles
```

例えば、OpenMediaVaultのIPが`10.0.0.10`の場合:
```bash
sudo mount -t nfs 10.0.0.10:/export/ShareFiles /mnt/ShareFiles
```

### 4. マウント確認
```bash
df -h | grep ShareFiles
ls -la /mnt/ShareFiles
```

## 起動時に自動マウント（推奨）

`/etc/fstab`に追加:
```bash
sudo nano /etc/fstab
```

以下の行を追加（IPアドレスは適宜変更）:
```
10.0.0.10:/export/ShareFiles /mnt/ShareFiles nfs defaults,_netdev 0 0
```

保存後、テスト:
```bash
sudo mount -a
```

## NFSのエクスポートパスを確認

もしマウントできない場合、OpenMediaVaultのエクスポートパスを確認:
```bash
showmount -e OpenMediaVaultのIPアドレス
```

OpenMediaVaultのIPアドレスを教えていただければ、具体的なコマンドを提示できます。

### 👤 Human (2025-11-19 23:23)

マウントしたフォルダの更新時間を確認したい。
数日に分けて更新時間をがわかるようにファイル数をカウントするスクリプト

### 🤖 Assistant (2025-11-19 23:24)

 マウントしたフォルダの更新時間を確認し、日付ごとにファイル数をカウントするスクリプトを作成します。

```bash
#!/bin/bash

# 対象ディレクトリ（引数で指定、デフォルトはカレントディレクトリ）
TARGET_DIR="${1:-.}"

echo "=== ファイル更新日時の集計 ==="
echo "対象ディレクトリ: $TARGET_DIR"
echo ""

# 更新日時（mtime）でグループ化してカウント
echo "【日付別ファイル数】"
find "$TARGET_DIR" -type f -printf '%TY-%Tm-%Td\n' | sort | uniq -c | sort -k2

echo ""
echo "【月別ファイル数】"
find "$TARGET_DIR" -type f -printf '%TY-%Tm\n' | sort | uniq -c | sort -k2

echo ""
echo "【年別ファイル数】"
find "$TARGET_DIR" -type f -printf '%TY\n' | sort | uniq -c | sort -k2

echo ""
echo "【合計ファイル数】"
find "$TARGET_DIR" -type f | wc -l
```

## 使い方

```bash
# スクリプトを保存
nano count_files_by_date.sh

# 実行権限を付与
chmod +x count_files_by_date.sh

# 実行
./count_files_by_date.sh /mnt/ShareFiles

# または現在のディレクトリ
./count_files_by_date.sh
```

## より詳細な集計スクリプト

```bash
#!/bin/bash

TARGET_DIR="${1:-.}"

echo "=== ファイル更新日時の詳細集計 ==="
echo "対象: $TARGET_DIR"
echo ""

# 日付別（直近30日）
echo "【直近30日間の日別ファイル数】"
for i in {0..29}; do
    date_str=$(date -d "$i days ago" +%Y-%m-%d)
    count=$(find "$TARGET_DIR" -type f -newermt "$date_str 00:00:00" ! -newermt "$date_str 23:59:59" 2>/dev/null | wc -l)
    if [ $count -gt 0 ]; then
        printf "%s: %5d files\n" "$date_str" "$count"
    fi
done

echo ""
echo "【期間別ファイル数】"
echo -n "今日: "
find "$TARGET_DIR" -type f -mtime 0 | wc -l

echo -n "昨日: "
find "$TARGET_DIR" -type f -mtime 1 | wc -l

echo -n "過去7日間: "
find "$TARGET_DIR" -type f -mtime -7 | wc -l

echo -n "過去30日間: "
find "$TARGET_DIR" -type f -mtime -30 | wc -l

echo -n "過去1年間: "
find "$TARGET_DIR" -type f -mtime -365 | wc -l

echo ""
echo "【最新・最古のファイル】"
echo -n "最新: "
find "$TARGET_DIR" -type f -printf '%T+ %p\n' | sort -r | head -1

echo -n "最古: "
find "$TARGET_DIR" -type f -printf '%T+ %p\n' | sort | head -1
```

## CSVで出力するバージョン

```bash
#!/bin/bash

TARGET_DIR="${1:-.}"
OUTPUT_CSV="file_count_$(date +%Y%m%d_%H%M%S).csv"

echo "日付,ファイル数" > "$OUTPUT_CSV"

find "$TARGET_DIR" -type f -printf '%TY-%Tm-%Td\n' | 
    sort | uniq -c | 
    awk '{print $2","$1}' >> "$OUTPUT_CSV"

echo "CSVファイルを作成しました: $OUTPUT_CSV"
cat "$OUTPUT_CSV"
```

どのスクリプトが用途に合いそうですか？必要に応じてカスタマイズもできます。

### 👤 Human (2025-11-19 23:31)

nas-serverのsyncが機能指定なさそう

### 🤖 Assistant (2025-11-19 23:31)

 OpenMediaVaultの同期機能が動いていないようですね。確認と対処方法を説明します。

## 確認すべきポイント

### 1. rsyncジョブの設定確認
OpenMediaVault管理画面で:
1. **「サービス」→「Rsync」→「ジョブ」**を開く
2. 設定したジョブが存在するか確認
3. ジョブの状態:
   - **有効化**されているか（チェックボックスがONか）
   - **スケジュール**設定が正しいか

### 2. rsyncサービスの状態確認
```bash
# OpenMediaVaultサーバーで実行
sudo systemctl status rsync
```

### 3. ログの確認
```bash
# rsyncのログを確認
sudo tail -f /var/log/rsync.log

# システムログも確認
sudo journalctl -u rsync -f

# OpenMediaVaultのログ
sudo tail -f /var/log/syslog | grep rsync
```

### 4. 手動で同期テスト
OpenMediaVault管理画面で:
1. ジョブを選択
2. **「実行」**ボタン（再生ボタン）をクリック
3. エラーメッセージが出るか確認

## よくある問題と対処法

### 問題1: ジョブが有効化されていない
- ジョブ一覧でチェックボックスをONにして保存

### 問題2: スケジュールが適切でない
- スケジュール設定を見直す（cron形式）
- テスト: 「毎分」に設定して動作確認後、適切な頻度に戻す

### 問題3: パーミッション・権限の問題
```bash
# 同期元のパーミッション確認
ls -la /srv/dev-disk-by-uuid-*/ShareFiles/

# rsyncユーザーの確認
id rsync
```

### 問題4: ネットワークの問題（リモート同期の場合）
```bash
# SSH接続テスト
ssh リモートホスト

# rsyncコマンドで手動テスト
rsync -avz /同期元/ /同期先/
```

## どのような同期を設定していますか？

以下を教えていただけると、より具体的にサポートできます:
1. **ローカル同期**（同じOpenMediaVault内）or **リモート同期**（別サーバーへ）
2. 同期元と同期先のパス
3. スケジュール設定（毎日、毎時など）
4. エラーメッセージが表示されているか

### 👤 Human (2025-11-20 23:19)

Cronが動いていない？
Rsyncのテスト実行はうまく行く。ただ自動実行がされないっぽい

### 🤖 Assistant (2025-11-20 23:19)

 Cronが動いていない可能性がありますね。確認と対処方法を説明します。

## 1. Cronサービスの状態確認

```bash
# cronサービスの状態確認
sudo systemctl status cron

# cronが起動していない場合は起動
sudo systemctl start cron
sudo systemctl enable cron
```

## 2. OpenMediaVaultのCron設定確認

OpenMediaVault管理画面で:
1. **「システム」→「スケジュール済みジョブ」**を開く
2. rsyncのジョブがリストに表示されているか確認
3. ジョブの詳細:
   - **有効**になっているか
   - **実行時刻**が正しく設定されているか

## 3. Crontabの直接確認

```bash
# rootのcrontabを確認
sudo crontab -l

# OpenMediaVaultのcron設定ファイルを確認
sudo cat /etc/cron.d/nas-server-*
ls -la /etc/cron.d/ | grep nas-server

# rsync関連のcronジョブを検索
sudo grep -r "rsync" /etc/cron.d/
```

## 4. Cronログの確認

```bash
# cronのログを確認（実行されているか）
sudo grep CRON /var/log/syslog | tail -20

# リアルタイムでログ監視
sudo tail -f /var/log/syslog | grep CRON
```

## 5. OpenMediaVaultの設定を再適用

管理画面で設定が反映されていない可能性があります:

```bash
# OpenMediaVaultの設定を再生成
sudo omv-salt deploy run rsync
sudo omv-salt deploy run cron

# または全体を再適用
sudo omv-salt deploy run --all
```

## 6. 手動でcronジョブを追加（最終手段）

もしOpenMediaVault経由で動かない場合:

```bash
# rootのcrontabを編集
sudo crontab -e

# 例: 毎日午前2時に実行
0 2 * * * rsync -avz /同期元/ /同期先/ >> /var/log/my-rsync.log 2>&1
```

## トラブルシューティング手順

```bash
# 1. cronが動いているか
sudo systemctl status cron

# 2. cronジョブが登録されているか
sudo crontab -l
sudo ls -la /etc/cron.d/

# 3. cronが実行されているか（ログで確認）
sudo grep CRON /var/log/syslog | tail -20

# 4. rsyncのスケジュールが有効か（OpenMediaVault管理画面で確認）

# 5. 設定を再適用
sudo omv-salt deploy run cron
```

これらを順番に確認してみてください。どこで止まっているか教えていただければ、より具体的に対処できます。

### 👤 Human (2025-11-20 23:22)

user@nas-server:~$ sudo systemctl status cron
[sudo] password for pi: 
● cron.service - Regular background program processing daemon
     Loaded: loaded (/lib/systemd/system/cron.service; enabled; preset: enabled)
     Active: active (running) since Tue 2025-11-11 23:23:56 UTC; 1 week 1 day ago
       Docs: man:cron(8)
   Main PID: 1786 (cron)
      Tasks: 1 (limit: 18968)
     Memory: 373.6M
        CPU: 54min 30.785s
     CGroup: /system.slice/cron.service
             └─1786 /usr/sbin/cron -f
Nov 20 23:09:01 nas-server CRON[834049]: pam_unix(cron:session): session opened for user root(uid=0) by (uid=0)
Nov 20 23:09:01 nas-server CRON[834050]: (root) CMD (  [ -x /usr/lib/php/sessionclean ] && if [ ! -d /run/systemd/system ]; then /usr/lib/php/sessionclean; fi)
Nov 20 23:09:01 nas-server CRON[834049]: pam_unix(cron:session): session closed for user root
Nov 20 23:15:01 nas-server CRON[835048]: pam_unix(cron:session): session opened for user root(uid=0) by (uid=0)
Nov 20 23:15:01 nas-server CRON[835049]: (root) CMD (/usr/sbin/omv-mkrrdgraph >/dev/null 2>&1)
Nov 20 23:15:05 nas-server CRON[835048]: pam_unix(cron:session): session closed for user root
Nov 20 23:17:01 nas-server CRON[837144]: pam_unix(cron:session): session opened for user root(uid=0) by (uid=0)
Nov 20 23:17:01 nas-server CRON[837145]: (root) CMD (cd / && run-parts --report /etc/cron.hourly)
Nov 20 23:17:01 nas-server omv-sfsnapadm[837148]: Start cleaning snapshots from shared folders ...
Nov 20 23:17:01 nas-server CRON[837144]: pam_unix(cron:session): session closed for user root



user@nas-server:~$ # rootのcrontabを確認
sudo crontab -l
# OpenMediaVaultのcron設定ファイルを確認
sudo cat /etc/cron.d/nas-server-*
ls -la /etc/cron.d/ | grep nas-server
# rsync関連のcronジョブを検索
sudo grep -r "rsync" /etc/cron.d/
no crontab for root
# Create graphs every 15 minutes
# m h dom mon dow user    command
*/15 * * * * root /usr/sbin/omv-mkrrdgraph >/dev/null 2>&1
# This file is auto-generated by nas-server (https://www.nas-server.org)
# WARNING: Do not edit this file, your changes will get lost.
SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
# m h dom mon dow user    command
10 3 1,10,20,21 * * root /var/lib/nas-server/cron.d/rsync-25e6bc1f-d2b4-4f96-9590-057b3b492216 2>&1 | grep -v '/$' | mail -E -s "Cron" -a "From: Cron Daemon <root>" root >/dev/null 2>&1
-rw-r--r--   1 root root   126 Sep  8 20:46 nas-server-mkrrdgraph
-rw-r--r--   1 root root   447 Nov 19 23:50 nas-server-rsync
/etc/cron.d/nas-server-rsync:10 3 1,10,20,21 * * root /var/lib/nas-server/cron.d/rsync-25e6bc1f-d2b4-4f96-9590-057b3b492216 2>&1 | grep -v '/$' | mail -E -s "Cron" -a "From: Cron Daemon <root>" root >/dev/null 2>&1

### 🤖 Assistant (2025-11-20 23:22)

 cronは動いていますね。rsyncのジョブも登録されています。スケジュールを見ると：

```
10 3 1,10,20,21 * * root ...
```

これは**毎月1日、10日、20日、21日の午前3時10分**に実行される設定になっています。

## 問題の原因

次の実行予定日が**12月1日の午前3時10分**なので、まだ実行されていないだけのようです。

## 確認と対処方法

### 1. 実行スクリプトの内容を確認

```bash
# 実際に実行されるスクリプトを確認
sudo cat /var/lib/nas-server/cron.d/rsync-25e6bc1f-d2b4-4f96-9590-057b3b492216
```

### 2. 手動でスクリプトを実行してテスト

```bash
# cronと同じように実行してみる
sudo /var/lib/nas-server/cron.d/rsync-25e6bc1f-d2b4-4f96-9590-057b3b492216
```

### 3. スケジュールを変更（もっと頻繁に実行したい場合）

OpenMediaVault管理画面で:
1. **「サービス」→「Rsync」→「ジョブ」**
2. 該当のジョブを選択して編集
3. **「スケジュール」**を変更:
   - **毎日実行**: `0 3 * * *` (毎日午前3時)
   - **毎時実行**: `0 * * * *` (毎時0分)
   - **テスト用**: `*/5 * * * *` (5分ごと)
4. 保存→適用

### 4. 次回実行を待たずにテスト

```bash
# テスト用にスケジュールを一時的に変更（5分ごと）
# OpenMediaVault管理画面で */5 * * * * に変更
# 5分待って実行されるか確認

# ログをリアルタイム監視
sudo tail -f /var/log/syslog | grep -E 'rsync|CRON'
```

### 5. メール通知の確認

cronの出力は`mail`コマンドでrootユーザーに送られる設定になっています:

```bash
# rootのメールを確認
sudo mail

# またはメールファイルを直接確認
sudo cat /var/mail/root
```

## 推奨される設定変更

もし毎日同期したい場合は、OpenMediaVault管理画面で：
- **分**: 10
- **時**: 3
- **日**: `*` (毎日)
- **月**: `*`
- **曜日**: `*`

これで**毎日午前3時10分**に実行されるようになります。

スケジュールを変更しますか？それとも現在の設定（月に4回）のままで良いですか？

### 👤 Human (2025-11-20 23:23)

### 🤖 Assistant (2025-11-20 23:23)

 完璧です！rsyncは正常に動作していますね。同期も成功しています。

## 状況の整理

✅ **cronサービス**: 正常に動作中
✅ **rsyncスクリプト**: 手動実行で正常に動作
✅ **同期処理**: 成功（195MB受信、約909TBの総サイズ）
✅ **cronジョブ**: 登録済み

**問題**: スケジュールが月4回（1, 10, 20, 21日の午前3:10）のみ実行

## 次回の自動実行予定

- **次回**: 2025年12月1日 午前3:10
- **その次**: 2025年12月10日 午前3:10

## より頻繁に実行したい場合の設定変更

OpenMediaVault管理画面で:

1. **「サービス」→「Rsync」→「ジョブ」**を開く
2. 該当のジョブを選択して**編集**（鉛筆アイコン）
3. **「スケジュール」**タブで以下のいずれかに変更:

### 推奨設定例

**毎日午前3時10分に実行:**
- 分: `10`
- 時: `3`
- 日: `*`
- 月: `*`
- 曜日: `*`

**毎週日曜日午前3時に実行:**
- 分: `0`
- 時: `3`
- 日: `*`
- 月: `*`
- 曜日: `0`

4. **保存**→画面上部の黄色い通知バーが出たら**適用**

## cronが正しく動作しているか確認（オプション）

次の実行日まで待てない場合、一時的に頻度を上げてテスト:

```bash
# 現在時刻を確認
date

# 例: 現在が15:30なら、15:35に実行されるように一時的に変更
# OpenMediaVault管理画面で「分」を35、「時」を15に変更して保存

# ログを監視
sudo tail -f /var/log/syslog | grep -E 'rsync|CRON'
```

実行を確認したら、元の適切なスケジュールに戻してください。

現在の設定（月4回）のままで良いですか？それとも毎日実行に変更しますか？

### 👤 Human (2025-11-20 23:24)

user@nas-server:~$ sudo mail
No mail for root
user@nas-server:~$ sudo cat /var/mail/root
cat: /var/mail/root: No such file or directory

### 🤖 Assistant (2025-11-20 23:24)

 メールシステムが設定されていないようですね。cronの実行結果がメールで通知される設定になっていますが、メールサーバーがないため届いていません。

## 対処方法

### 1. メール通知を無効化してログファイルに出力（推奨）

cronの設定を変更して、メールではなくログファイルに結果を保存します：

```bash
# 現在のcron設定を確認
sudo cat /etc/cron.d/nas-server-rsync

# 手動で編集（OpenMediaVaultで再生成されるので一時的）
sudo nano /etc/cron.d/nas-server-rsync
```

または、**OpenMediaVault管理画面で設定を変更**:

1. **「サービス」→「Rsync」→「ジョブ」**
2. 該当ジョブを編集
3. **「メール通知」や「Send command output via email」のチェックを外す**

### 2. ログファイルで実行履歴を確認

rsyncの実行履歴は以下で確認できます：

```bash
# cronの実行ログ
sudo grep "rsync-25e6bc1f" /var/log/syslog

# 直近の実行ログ
sudo grep "rsync-25e6bc1f" /var/log/syslog | tail -20

# 日付を指定して確認（例：12月1日以降）
sudo grep "rsync-25e6bc1f" /var/log/syslog | grep "Dec  1"
```

### 3. カスタムログファイルを作成

cronスクリプトを直接編集してログを残す方法：

```bash
# スクリプトを確認
sudo cat /var/lib/nas-server/cron.d/rsync-25e6bc1f-d2b4-4f96-9590-057b3b492216

# ログディレクトリを作成
sudo mkdir -p /var/log/rsync-jobs

# 次回の自動実行後にログを確認
sudo tail -f /var/log/syslog | grep rsync
```

### 4. メールシステムをインストール（オプション）

メール通知が必要な場合：

```bash
# 軽量メールシステムをインストール
sudo apt update
sudo apt install mailutils postfix

# postfixの設定: "Local only" を選択
```

## 推奨される確認方法

次回の自動実行（12月1日午前3:10）後に確認:

```bash
# 12月1日午前3:15頃に実行
sudo grep "rsync" /var/log/syslog | grep "Dec  1" | grep "03:"

# またはリアルタイム監視（12月1日午前3:00〜3:20）
sudo tail -f /var/log/syslog | grep -E 'rsync|CRON'
```

## すぐに動作確認したい場合

スケジュールを一時的に変更して数分後に実行させる：

```bash
# 現在時刻を確認
date

# OpenMediaVault管理画面で、現在時刻+5分後に実行されるように設定
# 例: 現在15:30なら、15:35に設定

# ログを監視
sudo tail -f /var/log/syslog | grep -E 'rsync|CRON'
```

メール通知は必要ですか？不要であれば、OpenMediaVault管理画面でメール通知をオフにするのが最もシンプルです。

### 👤 Human (2025-11-20 23:33)

画面での設定
<mat-card-content _ngcontent-yck-c56="" class="mat-card-content"><omv-intuition-form _ngcontent-yck-c56="" _nghost-yck-c53=""><form _ngcontent-yck-c53="" novalidate="" id="omv-intuition-form-9" class="ng-untouched ng-pristine ng-valid"><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></p><!----><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><omv-form-checkbox _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted ng-valid" _nghost-yck-c110=""><div _ngcontent-yck-c110="" class="omv-form-checkbox-wrapper mat-form-field omv-display-flex omv-flex-1 omv-flex-column ng-untouched ng-pristine ng-valid"><mat-checkbox _ngcontent-yck-c110="" class="mat-checkbox mat-accent mat-checkbox-checked ng-untouched ng-pristine ng-valid" id="mat-checkbox-48"><label class="mat-checkbox-layout" for="mat-checkbox-48-input"><span class="mat-checkbox-inner-container"><input type="checkbox" class="mat-checkbox-input cdk-visually-hidden" id="mat-checkbox-48-input" tabindex="0" aria-checked="true"><span matripple="" class="mat-ripple mat-checkbox-ripple mat-focus-indicator"><span class="mat-ripple-element mat-checkbox-persistent-ripple"></span></span><span class="mat-checkbox-frame"></span><span class="mat-checkbox-background"><svg version="1.1" focusable="false" viewBox="0 0 24 24" aria-hidden="true" class="mat-checkbox-checkmark"><path fill="none" stroke="white" d="M4.1,12.7 9,17.6 20.3,6.3" class="mat-checkbox-checkmark-path"></path></svg><span class="mat-checkbox-mixedmark"></span></span></span><span class="mat-checkbox-label"><span style="display: none;">&nbsp;</span> 有効 </span></label></mat-checkbox><!----><!----></div></omv-form-checkbox><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></p><!----><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><omv-form-select _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted ng-valid" _nghost-yck-c124=""><mat-form-field _ngcontent-yck-c124="" class="mat-form-field omv-flex-1 ng-tns-c65-131 mat-primary mat-form-field-type-mat-select mat-form-field-appearance-legacy mat-form-field-can-float mat-form-field-should-float mat-form-field-has-label ng-untouched ng-pristine ng-star-inserted ng-valid"><div class="mat-form-field-wrapper ng-tns-c65-131"><div class="mat-form-field-flex ng-tns-c65-131"><!----><!----><div class="mat-form-field-infix ng-tns-c65-131"><mat-select _ngcontent-yck-c124="" role="combobox" aria-autocomplete="none" aria-haspopup="true" class="mat-select ng-tns-c83-132 ng-tns-c65-131 ng-untouched ng-pristine ng-valid ng-star-inserted" aria-labelledby="mat-form-field-label-139 mat-select-value-69" id="mat-select-68" tabindex="0" aria-expanded="false" aria-required="false" aria-disabled="false" aria-invalid="false"><div cdk-overlay-origin="" class="mat-select-trigger ng-tns-c83-132"><div class="mat-select-value ng-tns-c83-132" id="mat-select-value-69"><!----><span class="mat-select-value-text ng-tns-c83-132 ng-star-inserted"><span class="mat-select-min-line ng-tns-c83-132 ng-star-inserted">リモート</span><!----><!----></span><!----></div><div class="mat-select-arrow-wrapper ng-tns-c83-132"><div class="mat-select-arrow ng-tns-c83-132"></div></div></div><!----></mat-select><span class="mat-form-field-label-wrapper ng-tns-c65-131"><label class="mat-form-field-label ng-tns-c65-131 ng-star-inserted" id="mat-form-field-label-139" for="mat-select-68" aria-owns="mat-select-68"><!----><mat-label _ngcontent-yck-c124="" class="ng-tns-c65-131 ng-star-inserted">タイプ</mat-label><!----><!----></label><!----></span></div><!----></div><div class="mat-form-field-underline ng-tns-c65-131 ng-star-inserted"><span class="mat-form-field-ripple ng-tns-c65-131"></span></div><!----><div class="mat-form-field-subscript-wrapper ng-tns-c65-131"><!----><div class="mat-form-field-hint-wrapper ng-tns-c65-131 ng-trigger ng-trigger-transitionMessages ng-star-inserted" style="opacity: 1; transform: translateY(0%);"><!----><!----><div class="mat-form-field-hint-spacer ng-tns-c65-131"></div></div><!----></div></div></mat-form-field></omv-form-select><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></p><!----><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><omv-form-select _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted ng-valid" _nghost-yck-c124=""><mat-form-field _ngcontent-yck-c124="" class="mat-form-field omv-flex-1 ng-tns-c65-133 mat-primary mat-form-field-type-mat-select mat-form-field-appearance-legacy mat-form-field-can-float mat-form-field-should-float mat-form-field-has-label ng-untouched ng-pristine ng-star-inserted ng-valid"><div class="mat-form-field-wrapper ng-tns-c65-133"><div class="mat-form-field-flex ng-tns-c65-133"><!----><!----><div class="mat-form-field-infix ng-tns-c65-133"><mat-select _ngcontent-yck-c124="" role="combobox" aria-autocomplete="none" aria-haspopup="true" class="mat-select ng-tns-c83-134 ng-tns-c65-133 ng-untouched ng-pristine ng-valid ng-star-inserted" aria-labelledby="mat-form-field-label-141 mat-select-value-71" id="mat-select-70" tabindex="0" aria-expanded="false" aria-required="false" aria-disabled="false" aria-invalid="false"><div cdk-overlay-origin="" class="mat-select-trigger ng-tns-c83-134"><div class="mat-select-value ng-tns-c83-134" id="mat-select-value-71"><!----><span class="mat-select-value-text ng-tns-c83-134 ng-star-inserted"><span class="mat-select-min-line ng-tns-c83-134 ng-star-inserted">プル</span><!----><!----></span><!----></div><div class="mat-select-arrow-wrapper ng-tns-c83-134"><div class="mat-select-arrow ng-tns-c83-134"></div></div></div><!----></mat-select><span class="mat-form-field-label-wrapper ng-tns-c65-133"><label class="mat-form-field-label ng-tns-c65-133 ng-star-inserted" id="mat-form-field-label-141" for="mat-select-70" aria-owns="mat-select-70"><!----><mat-label _ngcontent-yck-c124="" class="ng-tns-c65-133 ng-star-inserted">モード</mat-label><!----><!----></label><!----></span></div><!----></div><div class="mat-form-field-underline ng-tns-c65-133 ng-star-inserted"><span class="mat-form-field-ripple ng-tns-c65-133"></span></div><!----><div class="mat-form-field-subscript-wrapper ng-tns-c65-133"><!----><div class="mat-form-field-hint-wrapper ng-tns-c65-133 ng-trigger ng-trigger-transitionMessages ng-star-inserted" style="opacity: 1; transform: translateY(0%);"><!----><!----><div class="mat-form-field-hint-spacer ng-tns-c65-133"></div></div><!----></div></div></mat-form-field></omv-form-select><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></p><!----><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><omv-form-sharedfolder-select _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted omv-display-none ng-valid" _nghost-yck-c125=""><mat-form-field _ngcontent-yck-c125="" class="mat-form-field omv-flex-1 ng-tns-c65-135 mat-primary mat-form-field-type-mat-select mat-form-field-appearance-legacy mat-form-field-can-float mat-form-field-should-float mat-form-field-has-label ng-untouched ng-pristine ng-star-inserted ng-valid"><div class="mat-form-field-wrapper ng-tns-c65-135"><div class="mat-form-field-flex ng-tns-c65-135"><!----><!----><div class="mat-form-field-infix ng-tns-c65-135"><mat-select _ngcontent-yck-c125="" role="combobox" aria-autocomplete="none" aria-haspopup="true" class="mat-select ng-tns-c83-136 ng-tns-c65-135 ng-untouched ng-pristine ng-star-inserted ng-valid" aria-labelledby="mat-form-field-label-143 mat-select-value-73" id="mat-select-72" tabindex="0" aria-expanded="false" aria-required="false" aria-disabled="false" aria-invalid="false"><div cdk-overlay-origin="" class="mat-select-trigger ng-tns-c83-136"><div class="mat-select-value ng-tns-c83-136" id="mat-select-value-73"><!----><span class="mat-select-value-text ng-tns-c83-136 ng-star-inserted"><span class="mat-select-min-line ng-tns-c83-136 ng-star-inserted">None</span><!----><!----></span><!----></div><div class="mat-select-arrow-wrapper ng-tns-c83-136"><div class="mat-select-arrow ng-tns-c83-136"></div></div></div><!----></mat-select><span class="mat-form-field-label-wrapper ng-tns-c65-135"><label class="mat-form-field-label ng-tns-c65-135 ng-star-inserted" id="mat-form-field-label-143" for="mat-select-72" aria-owns="mat-select-72"><!----><mat-label _ngcontent-yck-c125="" class="ng-tns-c65-135 ng-star-inserted">ソース共有フォルダ</mat-label><!----><!----></label><!----></span></div><div class="mat-form-field-suffix ng-tns-c65-135 ng-star-inserted"><mat-icon _ngcontent-yck-c125="" role="img" matsuffix="" svgicon="mdi:plus-circle-outline" class="mat-icon notranslate mat-tooltip-trigger mat-icon-no-color ng-tns-c65-135 ng-star-inserted" aria-hidden="true" data-mat-icon-type="svg" data-mat-icon-name="plus-circle-outline" data-mat-icon-namespace="mdi" aria-describedby="cdk-describedby-message-yck-1-83" cdk-describedby-host="yck-1"><svg viewBox="0 0 24 24" fit="" height="100%" width="100%" preserveAspectRatio="xMidYMid meet" focusable="false"><path d="M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M13,7H11V11H7V13H11V17H13V13H17V11H13V7Z"></path></svg></mat-icon><!----><!----></div><!----></div><div class="mat-form-field-underline ng-tns-c65-135 ng-star-inserted"><span class="mat-form-field-ripple ng-tns-c65-135"></span></div><!----><div class="mat-form-field-subscript-wrapper ng-tns-c65-135"><!----><div class="mat-form-field-hint-wrapper ng-tns-c65-135 ng-trigger ng-trigger-transitionMessages ng-star-inserted" style="opacity: 1; transform: translateY(0%);"><!----><!----><div class="mat-form-field-hint-spacer ng-tns-c65-135"></div></div><!----></div></div></mat-form-field></omv-form-sharedfolder-select><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></p><!----><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><omv-form-text-input _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted ng-valid" _nghost-yck-c131=""><mat-form-field _ngcontent-yck-c131="" class="mat-form-field omv-flex-1 ng-tns-c65-137 mat-primary mat-form-field-type-mat-input mat-form-field-appearance-legacy mat-form-field-can-float mat-form-field-should-float mat-form-field-has-label ng-untouched ng-pristine ng-star-inserted ng-valid"><div class="mat-form-field-wrapper ng-tns-c65-137"><div class="mat-form-field-flex ng-tns-c65-137"><!----><!----><div class="mat-form-field-infix ng-tns-c65-137"><input _ngcontent-yck-c131="" matinput="" type="text" class="mat-autocomplete-trigger mat-input-element mat-form-field-autofill-control omv-text-truncate ng-tns-c65-137 ng-untouched ng-pristine ng-valid cdk-text-field-autofill-monitored" autocapitalize="none" aria-describedby="mat-hint-39" id="mat-input-30" aria-invalid="false" aria-required="true" required=""><!----><mat-autocomplete _ngcontent-yck-c131="" autoactivefirstoption="" class="mat-autocomplete ng-tns-c65-137"><!----></mat-autocomplete><span class="mat-form-field-label-wrapper ng-tns-c65-137"><label class="mat-form-field-label ng-tns-c65-137 ng-star-inserted" id="mat-form-field-label-145" for="mat-input-30" aria-owns="mat-input-30"><!----><mat-label _ngcontent-yck-c131="" class="ng-tns-c65-137 ng-star-inserted">ソースサーバ</mat-label><!----><span aria-hidden="true" class="mat-placeholder-required mat-form-field-required-marker ng-tns-c65-137 ng-star-inserted"> *</span><!----></label><!----></span></div><!----></div><div class="mat-form-field-underline ng-tns-c65-137 ng-star-inserted"><span class="mat-form-field-ripple ng-tns-c65-137"></span></div><!----><div class="mat-form-field-subscript-wrapper ng-tns-c65-137"><!----><div class="mat-form-field-hint-wrapper ng-tns-c65-137 ng-trigger ng-trigger-transitionMessages ng-star-inserted" style="opacity: 1; transform: translateY(0%);"><!----><mat-hint _ngcontent-yck-c131="" class="mat-hint ng-tns-c65-137 ng-star-inserted" id="mat-hint-39" style="">送信元リモートサーバ 例） [USER@]HOST:SRC, [USER@]HOST::SRC または rsync://[USER@]HOST[:PORT]/SRC。</mat-hint><!----><div class="mat-form-field-hint-spacer ng-tns-c65-137"></div></div><!----></div></div></mat-form-field></omv-form-text-input><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></p><!----><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><omv-form-sharedfolder-select _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted ng-valid" _nghost-yck-c125=""><mat-form-field _ngcontent-yck-c125="" class="mat-form-field omv-flex-1 ng-tns-c65-138 mat-primary mat-form-field-type-mat-select mat-form-field-appearance-legacy mat-form-field-can-float mat-form-field-should-float mat-form-field-has-label ng-untouched ng-pristine ng-star-inserted ng-valid"><div class="mat-form-field-wrapper ng-tns-c65-138"><div class="mat-form-field-flex ng-tns-c65-138"><!----><!----><div class="mat-form-field-infix ng-tns-c65-138"><mat-select _ngcontent-yck-c125="" role="combobox" aria-autocomplete="none" aria-haspopup="true" class="mat-select ng-tns-c83-139 ng-tns-c65-138 mat-select-required ng-untouched ng-pristine ng-star-inserted ng-valid" aria-labelledby="mat-form-field-label-147 mat-select-value-75" id="mat-select-74" tabindex="0" aria-expanded="false" aria-required="true" aria-disabled="false" aria-invalid="false" required=""><div cdk-overlay-origin="" class="mat-select-trigger ng-tns-c83-139"><div class="mat-select-value ng-tns-c83-139" id="mat-select-value-75"><!----><span class="mat-select-value-text ng-tns-c83-139 ng-star-inserted"><span class="mat-select-min-line ng-tns-c83-139 ng-star-inserted">Backup [on /dev/sdb1, Backup/]</span><!----><!----></span><!----></div><div class="mat-select-arrow-wrapper ng-tns-c83-139"><div class="mat-select-arrow ng-tns-c83-139"></div></div></div><!----></mat-select><span class="mat-form-field-label-wrapper ng-tns-c65-138"><label class="mat-form-field-label ng-tns-c65-138 ng-star-inserted" id="mat-form-field-label-147" for="mat-select-74" aria-owns="mat-select-74"><!----><mat-label _ngcontent-yck-c125="" class="ng-tns-c65-138 ng-star-inserted">送信先共有フォルダ</mat-label><!----><span aria-hidden="true" class="mat-placeholder-required mat-form-field-required-marker ng-tns-c65-138 ng-star-inserted"> *</span><!----></label><!----></span></div><div class="mat-form-field-suffix ng-tns-c65-138 ng-star-inserted"><mat-icon _ngcontent-yck-c125="" role="img" matsuffix="" svgicon="mdi:plus-circle-outline" class="mat-icon notranslate mat-tooltip-trigger mat-icon-no-color ng-tns-c65-138 ng-star-inserted" aria-hidden="true" data-mat-icon-type="svg" data-mat-icon-name="plus-circle-outline" data-mat-icon-namespace="mdi" aria-describedby="cdk-describedby-message-yck-1-83" cdk-describedby-host="yck-1"><svg viewBox="0 0 24 24" fit="" height="100%" width="100%" preserveAspectRatio="xMidYMid meet" focusable="false"><path d="M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M13,7H11V11H7V13H11V17H13V13H17V11H13V7Z"></path></svg></mat-icon><!----><!----></div><!----></div><div class="mat-form-field-underline ng-tns-c65-138 ng-star-inserted"><span class="mat-form-field-ripple ng-tns-c65-138"></span></div><!----><div class="mat-form-field-subscript-wrapper ng-tns-c65-138"><!----><div class="mat-form-field-hint-wrapper ng-tns-c65-138 ng-trigger ng-trigger-transitionMessages ng-star-inserted" style="opacity: 1; transform: translateY(0%);"><!----><!----><div class="mat-form-field-hint-spacer ng-tns-c65-138"></div></div><!----></div></div></mat-form-field></omv-form-sharedfolder-select><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></p><!----><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><omv-form-text-input _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted omv-display-none ng-valid" _nghost-yck-c131=""><mat-form-field _ngcontent-yck-c131="" class="mat-form-field omv-flex-1 ng-tns-c65-140 mat-primary mat-form-field-type-mat-input mat-form-field-appearance-legacy mat-form-field-can-float mat-form-field-should-float mat-form-field-has-label ng-untouched ng-pristine ng-star-inserted ng-valid"><div class="mat-form-field-wrapper ng-tns-c65-140"><div class="mat-form-field-flex ng-tns-c65-140"><!----><!----><div class="mat-form-field-infix ng-tns-c65-140"><input _ngcontent-yck-c131="" matinput="" type="text" class="mat-autocomplete-trigger mat-input-element mat-form-field-autofill-control omv-text-truncate ng-tns-c65-140 ng-untouched ng-pristine ng-valid cdk-text-field-autofill-monitored" autocapitalize="none" aria-describedby="mat-hint-40" id="mat-input-31" aria-invalid="false" aria-required="false"><!----><mat-autocomplete _ngcontent-yck-c131="" autoactivefirstoption="" class="mat-autocomplete ng-tns-c65-140"><!----></mat-autocomplete><span class="mat-form-field-label-wrapper ng-tns-c65-140"><label class="mat-form-field-label ng-tns-c65-140 ng-star-inserted" id="mat-form-field-label-149" for="mat-input-31" aria-owns="mat-input-31"><!----><mat-label _ngcontent-yck-c131="" class="ng-tns-c65-140 ng-star-inserted">送信先サーバ</mat-label><!----><!----></label><!----></span></div><!----></div><div class="mat-form-field-underline ng-tns-c65-140 ng-star-inserted"><span class="mat-form-field-ripple ng-tns-c65-140"></span></div><!----><div class="mat-form-field-subscript-wrapper ng-tns-c65-140"><!----><div class="mat-form-field-hint-wrapper ng-tns-c65-140 ng-trigger ng-trigger-transitionMessages ng-star-inserted" style="opacity: 1; transform: translateY(0%);"><!----><mat-hint _ngcontent-yck-c131="" class="mat-hint ng-tns-c65-140 ng-star-inserted" id="mat-hint-40" style="">送信先のリモートサーバ 例） [USER@]HOST:DEST, [USER@]HOST::DEST または rsync://[USER@]HOST[:PORT]/DEST。</mat-hint><!----><div class="mat-form-field-hint-spacer ng-tns-c65-140"></div></div><!----></div></div></mat-form-field></omv-form-text-input><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></p><!----><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><omv-form-select _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted ng-valid" _nghost-yck-c124=""><mat-form-field _ngcontent-yck-c124="" class="mat-form-field omv-flex-1 ng-tns-c65-141 mat-primary mat-form-field-type-mat-select mat-form-field-appearance-legacy mat-form-field-can-float mat-form-field-should-float mat-form-field-has-label ng-untouched ng-pristine ng-star-inserted ng-valid"><div class="mat-form-field-wrapper ng-tns-c65-141"><div class="mat-form-field-flex ng-tns-c65-141"><!----><!----><div class="mat-form-field-infix ng-tns-c65-141"><mat-select _ngcontent-yck-c124="" role="combobox" aria-autocomplete="none" aria-haspopup="true" class="mat-select ng-tns-c83-142 ng-tns-c65-141 ng-untouched ng-pristine ng-valid ng-star-inserted" aria-labelledby="mat-form-field-label-151 mat-select-value-77" id="mat-select-76" tabindex="0" aria-expanded="false" aria-required="false" aria-disabled="false" aria-invalid="false"><div cdk-overlay-origin="" class="mat-select-trigger ng-tns-c83-142"><div class="mat-select-value ng-tns-c83-142" id="mat-select-value-77"><!----><span class="mat-select-value-text ng-tns-c83-142 ng-star-inserted"><span class="mat-select-min-line ng-tns-c83-142 ng-star-inserted">公開鍵</span><!----><!----></span><!----></div><div class="mat-select-arrow-wrapper ng-tns-c83-142"><div class="mat-select-arrow ng-tns-c83-142"></div></div></div><!----></mat-select><span class="mat-form-field-label-wrapper ng-tns-c65-141"><label class="mat-form-field-label ng-tns-c65-141 ng-star-inserted" id="mat-form-field-label-151" for="mat-select-76" aria-owns="mat-select-76"><!----><mat-label _ngcontent-yck-c124="" class="ng-tns-c65-141 ng-star-inserted">認証</mat-label><!----><!----></label><!----></span></div><!----></div><div class="mat-form-field-underline ng-tns-c65-141 ng-star-inserted"><span class="mat-form-field-ripple ng-tns-c65-141"></span></div><!----><div class="mat-form-field-subscript-wrapper ng-tns-c65-141"><!----><div class="mat-form-field-hint-wrapper ng-tns-c65-141 ng-trigger ng-trigger-transitionMessages ng-star-inserted" style="opacity: 1; transform: translateY(0%);"><!----><!----><div class="mat-form-field-hint-spacer ng-tns-c65-141"></div></div><!----></div></div></mat-form-field></omv-form-select><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></p><!----><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><!----><!----><omv-form-number-input _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted ng-valid" _nghost-yck-c121=""><mat-form-field _ngcontent-yck-c121="" class="mat-form-field omv-flex-1 ng-tns-c65-143 mat-primary mat-form-field-type-mat-input mat-form-field-appearance-legacy mat-form-field-can-float mat-form-field-should-float mat-form-field-has-label ng-untouched ng-pristine ng-star-inserted ng-valid"><div class="mat-form-field-wrapper ng-tns-c65-143"><div class="mat-form-field-flex ng-tns-c65-143"><!----><!----><div class="mat-form-field-infix ng-tns-c65-143"><input _ngcontent-yck-c121="" matinput="" type="number" class="mat-input-element mat-form-field-autofill-control ng-tns-c65-143 ng-untouched ng-pristine ng-valid cdk-text-field-autofill-monitored" autocomplete="undefined" step="undefined" id="mat-input-32" aria-invalid="false" aria-required="true" min="1" max="65535" required=""><span class="mat-form-field-label-wrapper ng-tns-c65-143"><label class="mat-form-field-label ng-tns-c65-143 ng-star-inserted" id="mat-form-field-label-153" for="mat-input-32" aria-owns="mat-input-32"><!----><mat-label _ngcontent-yck-c121="" class="ng-tns-c65-143 ng-star-inserted">SSH ポート</mat-label><!----><span aria-hidden="true" class="mat-placeholder-required mat-form-field-required-marker ng-tns-c65-143 ng-star-inserted"> *</span><!----></label><!----></span></div><!----></div><div class="mat-form-field-underline ng-tns-c65-143 ng-star-inserted"><span class="mat-form-field-ripple ng-tns-c65-143"></span></div><!----><div class="mat-form-field-subscript-wrapper ng-tns-c65-143"><!----><div class="mat-form-field-hint-wrapper ng-tns-c65-143 ng-trigger ng-trigger-transitionMessages ng-star-inserted" style="opacity: 1; transform: translateY(0%);"><!----><!----><div class="mat-form-field-hint-spacer ng-tns-c65-143"></div></div><!----></div></div></mat-form-field></omv-form-number-input><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></p><!----><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><omv-form-sshcert-select _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted ng-valid" _nghost-yck-c127=""><mat-form-field _ngcontent-yck-c127="" class="mat-form-field omv-flex-1 ng-tns-c65-144 mat-primary mat-form-field-type-mat-select mat-form-field-appearance-legacy mat-form-field-can-float mat-form-field-should-float mat-form-field-has-label ng-untouched ng-pristine ng-star-inserted ng-valid"><div class="mat-form-field-wrapper ng-tns-c65-144"><div class="mat-form-field-flex ng-tns-c65-144"><!----><!----><div class="mat-form-field-infix ng-tns-c65-144"><mat-select _ngcontent-yck-c127="" role="combobox" aria-autocomplete="none" aria-haspopup="true" class="mat-select ng-tns-c83-145 ng-tns-c65-144 ng-untouched ng-pristine ng-valid ng-star-inserted mat-select-required" aria-labelledby="mat-form-field-label-155 mat-select-value-79" aria-describedby="mat-hint-41" id="mat-select-78" tabindex="0" aria-expanded="false" aria-required="true" aria-disabled="false" aria-invalid="false" required=""><div cdk-overlay-origin="" class="mat-select-trigger ng-tns-c83-145"><div class="mat-select-value ng-tns-c83-145" id="mat-select-value-79"><!----><span class="mat-select-value-text ng-tns-c83-145 ng-star-inserted"><span class="mat-select-min-line ng-tns-c83-145 ng-star-inserted">nas</span><!----><!----></span><!----></div><div class="mat-select-arrow-wrapper ng-tns-c83-145"><div class="mat-select-arrow ng-tns-c83-145"></div></div></div><!----></mat-select><span class="mat-form-field-label-wrapper ng-tns-c65-144"><label class="mat-form-field-label ng-tns-c65-144 ng-star-inserted" id="mat-form-field-label-155" for="mat-select-78" aria-owns="mat-select-78"><!----><mat-label _ngcontent-yck-c127="" class="ng-tns-c65-144 ng-star-inserted">SSH証明書</mat-label><!----><span aria-hidden="true" class="mat-placeholder-required mat-form-field-required-marker ng-tns-c65-144 ng-star-inserted"> *</span><!----></label><!----></span></div><div class="mat-form-field-suffix ng-tns-c65-144 ng-star-inserted"><mat-icon _ngcontent-yck-c127="" role="img" matsuffix="" svgicon="mdi:plus-circle-outline" class="mat-icon notranslate mat-tooltip-trigger mat-icon-no-color ng-tns-c65-144 ng-star-inserted" aria-hidden="true" data-mat-icon-type="svg" data-mat-icon-name="plus-circle-outline" data-mat-icon-namespace="mdi" aria-describedby="cdk-describedby-message-yck-1-83" cdk-describedby-host="yck-1"><svg viewBox="0 0 24 24" fit="" height="100%" width="100%" preserveAspectRatio="xMidYMid meet" focusable="false"><path d="M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M13,7H11V11H7V13H11V17H13V13H17V11H13V7Z"></path></svg></mat-icon><!----><!----></div><!----></div><div class="mat-form-field-underline ng-tns-c65-144 ng-star-inserted"><span class="mat-form-field-ripple ng-tns-c65-144"></span></div><!----><div class="mat-form-field-subscript-wrapper ng-tns-c65-144"><!----><div class="mat-form-field-hint-wrapper ng-tns-c65-144 ng-trigger ng-trigger-transitionMessages ng-star-inserted" style="opacity: 1; transform: translateY(0%);"><!----><mat-hint _ngcontent-yck-c127="" class="mat-hint ng-tns-c65-144 ng-star-inserted" id="mat-hint-41" style="">SSH証明書が認証に使用されます。</mat-hint><!----><div class="mat-form-field-hint-spacer ng-tns-c65-144"></div></div><!----></div></div></mat-form-field></omv-form-sshcert-select><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></p><!----><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><!----><omv-form-password-input _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted omv-display-none ng-valid" _nghost-yck-c123=""><mat-form-field _ngcontent-yck-c123="" class="mat-form-field omv-flex-1 ng-tns-c65-146 mat-primary mat-form-field-type-mat-input mat-form-field-appearance-legacy mat-form-field-can-float mat-form-field-should-float mat-form-field-has-label ng-untouched ng-pristine ng-star-inserted ng-valid"><div class="mat-form-field-wrapper ng-tns-c65-146"><div class="mat-form-field-flex ng-tns-c65-146"><!----><!----><div class="mat-form-field-infix ng-tns-c65-146"><input _ngcontent-yck-c123="" matinput="" type="password" autocorrect="off" class="mat-input-element mat-form-field-autofill-control ng-tns-c65-146 ng-untouched ng-pristine ng-valid cdk-text-field-autofill-monitored" autocomplete="new-password" autocapitalize="none" aria-describedby="mat-hint-42" id="mat-input-33" aria-invalid="false" aria-required="false"><span class="mat-form-field-label-wrapper ng-tns-c65-146"><label class="mat-form-field-label ng-tns-c65-146 ng-star-inserted" id="mat-form-field-label-157" for="mat-input-33" aria-owns="mat-input-33"><!----><mat-label _ngcontent-yck-c123="" class="ng-tns-c65-146 ng-star-inserted">パスワード</mat-label><!----><!----></label><!----></span></div><div class="mat-form-field-suffix ng-tns-c65-146 ng-star-inserted"><mat-icon _ngcontent-yck-c123="" role="img" matsuffix="" svgicon="mdi:eye-outline" class="mat-icon notranslate mat-tooltip-trigger mat-icon-no-color ng-tns-c65-146" aria-hidden="true" data-mat-icon-type="svg" data-mat-icon-name="eye-outline" data-mat-icon-namespace="mdi" aria-describedby="cdk-describedby-message-yck-1-84" cdk-describedby-host="yck-1"><svg viewBox="0 0 24 24" fit="" height="100%" width="100%" preserveAspectRatio="xMidYMid meet" focusable="false"><path d="M12,9A3,3 0 0,1 15,12A3,3 0 0,1 12,15A3,3 0 0,1 9,12A3,3 0 0,1 12,9M12,4.5C17,4.5 21.27,7.61 23,12C21.27,16.39 17,19.5 12,19.5C7,19.5 2.73,16.39 1,12C2.73,7.61 7,4.5 12,4.5M3.18,12C4.83,15.36 8.24,17.5 12,17.5C15.76,17.5 19.17,15.36 20.82,12C19.17,8.64 15.76,6.5 12,6.5C8.24,6.5 4.83,8.64 3.18,12Z"></path></svg></mat-icon><!----><!----></div><!----></div><div class="mat-form-field-underline ng-tns-c65-146 ng-star-inserted"><span class="mat-form-field-ripple ng-tns-c65-146"></span></div><!----><div class="mat-form-field-subscript-wrapper ng-tns-c65-146"><!----><div class="mat-form-field-hint-wrapper ng-tns-c65-146 ng-trigger ng-trigger-transitionMessages ng-star-inserted" style="opacity: 1; transform: translateY(0%);"><!----><mat-hint _ngcontent-yck-c123="" class="mat-hint ng-tns-c65-146 ng-star-inserted" id="mat-hint-42" style="">rsync デーモン経由のアクセスに使用されるパスワードです。SSHのようなリモートシェル転送では使用されないことに注意してください。</mat-hint><!----><div class="mat-form-field-hint-spacer ng-tns-c65-146"></div></div><!----></div></div></mat-form-field></omv-form-password-input><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></p><!----><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><omv-form-text-input _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted ng-valid" _nghost-yck-c131=""><mat-form-field _ngcontent-yck-c131="" class="mat-form-field omv-flex-1 ng-tns-c65-147 mat-primary mat-form-field-type-mat-input mat-form-field-appearance-legacy mat-form-field-can-float mat-form-field-should-float mat-form-field-has-label mat-form-field-disabled ng-untouched ng-pristine ng-star-inserted ng-valid"><div class="mat-form-field-wrapper ng-tns-c65-147"><div class="mat-form-field-flex ng-tns-c65-147"><!----><!----><div class="mat-form-field-infix ng-tns-c65-147"><input _ngcontent-yck-c131="" matinput="" type="text" class="mat-autocomplete-trigger mat-input-element mat-form-field-autofill-control omv-text-truncate ng-tns-c65-147 ng-untouched ng-pristine cdk-text-field-autofill-monitored" autocapitalize="none" disabled="" id="mat-input-34" aria-invalid="false" aria-required="false"><!----><mat-autocomplete _ngcontent-yck-c131="" autoactivefirstoption="" class="mat-autocomplete ng-tns-c65-147"><!----></mat-autocomplete><span class="mat-form-field-label-wrapper ng-tns-c65-147"><label class="mat-form-field-label ng-tns-c65-147 ng-star-inserted" id="mat-form-field-label-159" for="mat-input-34" aria-owns="mat-input-34"><!----><mat-label _ngcontent-yck-c131="" class="ng-tns-c65-147 ng-star-inserted">実行時刻</mat-label><!----><!----></label><!----></span></div><!----></div><div class="mat-form-field-underline ng-tns-c65-147 ng-star-inserted"><span class="mat-form-field-ripple ng-tns-c65-147"></span></div><!----><div class="mat-form-field-subscript-wrapper ng-tns-c65-147"><!----><div class="mat-form-field-hint-wrapper ng-tns-c65-147 ng-trigger ng-trigger-transitionMessages ng-star-inserted" style="opacity: 1; transform: translateY(0%);"><!----><!----><div class="mat-form-field-hint-spacer ng-tns-c65-147"></div></div><!----></div></div></mat-form-field></omv-form-text-input><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></p><!----><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><div _ngcontent-yck-c53="" class="omv-form-container omv-box-border omv-display-flex omv-flex-row omv-flex-wrap omv-gap-3 omv-align-items-stretch ng-star-inserted"><div _ngcontent-yck-c53="" class="omv-form-container-item omv-flex-1 ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><omv-form-select _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted ng-valid" _nghost-yck-c124=""><mat-form-field _ngcontent-yck-c124="" class="mat-form-field omv-flex-1 ng-tns-c65-148 mat-primary mat-form-field-type-mat-select mat-form-field-appearance-legacy mat-form-field-can-float mat-form-field-should-float mat-form-field-has-label ng-untouched ng-pristine ng-star-inserted ng-valid"><div class="mat-form-field-wrapper ng-tns-c65-148"><div class="mat-form-field-flex ng-tns-c65-148"><!----><!----><div class="mat-form-field-infix ng-tns-c65-148"><mat-select _ngcontent-yck-c124="" role="combobox" aria-autocomplete="none" aria-haspopup="true" class="mat-select ng-tns-c83-149 ng-tns-c65-148 mat-select-required mat-select-multiple ng-untouched ng-pristine ng-valid ng-star-inserted" aria-labelledby="mat-form-field-label-161 mat-select-value-81" id="mat-select-80" tabindex="0" aria-expanded="false" aria-required="true" aria-disabled="false" aria-invalid="false" required=""><div cdk-overlay-origin="" class="mat-select-trigger ng-tns-c83-149"><div class="mat-select-value ng-tns-c83-149" id="mat-select-value-81"><!----><span class="mat-select-value-text ng-tns-c83-149 ng-star-inserted"><span class="mat-select-min-line ng-tns-c83-149 ng-star-inserted">10</span><!----><!----></span><!----></div><div class="mat-select-arrow-wrapper ng-tns-c83-149"><div class="mat-select-arrow ng-tns-c83-149"></div></div></div><!----></mat-select><span class="mat-form-field-label-wrapper ng-tns-c65-148"><label class="mat-form-field-label ng-tns-c65-148 ng-star-inserted" id="mat-form-field-label-161" for="mat-select-80" aria-owns="mat-select-80"><!----><mat-label _ngcontent-yck-c124="" class="ng-tns-c65-148 ng-star-inserted">分</mat-label><!----><span aria-hidden="true" class="mat-placeholder-required mat-form-field-required-marker ng-tns-c65-148 ng-star-inserted"> *</span><!----></label><!----></span></div><!----></div><div class="mat-form-field-underline ng-tns-c65-148 ng-star-inserted"><span class="mat-form-field-ripple ng-tns-c65-148"></span></div><!----><div class="mat-form-field-subscript-wrapper ng-tns-c65-148"><!----><div class="mat-form-field-hint-wrapper ng-tns-c65-148 ng-trigger ng-trigger-transitionMessages ng-star-inserted" style="opacity: 1; transform: translateY(0%);"><!----><!----><div class="mat-form-field-hint-spacer ng-tns-c65-148"></div></div><!----></div></div></mat-form-field></omv-form-select><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></div><div _ngcontent-yck-c53="" class="omv-form-container-item omv-flex-1 ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><omv-form-checkbox _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted ng-valid" _nghost-yck-c110=""><div _ngcontent-yck-c110="" class="omv-form-checkbox-wrapper mat-form-field omv-display-flex omv-flex-1 omv-flex-column ng-untouched ng-pristine ng-valid"><mat-checkbox _ngcontent-yck-c110="" class="mat-checkbox mat-accent ng-untouched ng-pristine ng-valid" id="mat-checkbox-49"><label class="mat-checkbox-layout" for="mat-checkbox-49-input"><span class="mat-checkbox-inner-container"><input type="checkbox" class="mat-checkbox-input cdk-visually-hidden" id="mat-checkbox-49-input" tabindex="0" aria-checked="false"><span matripple="" class="mat-ripple mat-checkbox-ripple mat-focus-indicator"><span class="mat-ripple-element mat-checkbox-persistent-ripple"></span></span><span class="mat-checkbox-frame"></span><span class="mat-checkbox-background"><svg version="1.1" focusable="false" viewBox="0 0 24 24" aria-hidden="true" class="mat-checkbox-checkmark"><path fill="none" stroke="white" d="M4.1,12.7 9,17.6 20.3,6.3" class="mat-checkbox-checkmark-path"></path></svg><span class="mat-checkbox-mixedmark"></span></span></span><span class="mat-checkbox-label"><span style="display: none;">&nbsp;</span> 毎N分 </span></label></mat-checkbox><!----><!----></div></omv-form-checkbox><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></div><!----></div><!----><!----><!----><!----><!----><!----><!----></p><!----><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><div _ngcontent-yck-c53="" class="omv-form-container omv-box-border omv-display-flex omv-flex-row omv-flex-wrap omv-gap-3 omv-align-items-stretch ng-star-inserted"><div _ngcontent-yck-c53="" class="omv-form-container-item omv-flex-1 ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><omv-form-select _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted ng-valid" _nghost-yck-c124=""><mat-form-field _ngcontent-yck-c124="" class="mat-form-field omv-flex-1 ng-tns-c65-150 mat-primary mat-form-field-type-mat-select mat-form-field-appearance-legacy mat-form-field-can-float mat-form-field-should-float mat-form-field-has-label ng-untouched ng-pristine ng-star-inserted ng-valid"><div class="mat-form-field-wrapper ng-tns-c65-150"><div class="mat-form-field-flex ng-tns-c65-150"><!----><!----><div class="mat-form-field-infix ng-tns-c65-150"><mat-select _ngcontent-yck-c124="" role="combobox" aria-autocomplete="none" aria-haspopup="true" class="mat-select ng-tns-c83-151 ng-tns-c65-150 mat-select-required mat-select-multiple ng-untouched ng-pristine ng-valid ng-star-inserted" aria-labelledby="mat-form-field-label-163 mat-select-value-83" id="mat-select-82" tabindex="0" aria-expanded="false" aria-required="true" aria-disabled="false" aria-invalid="false" required=""><div cdk-overlay-origin="" class="mat-select-trigger ng-tns-c83-151"><div class="mat-select-value ng-tns-c83-151" id="mat-select-value-83"><!----><span class="mat-select-value-text ng-tns-c83-151 ng-star-inserted"><span class="mat-select-min-line ng-tns-c83-151 ng-star-inserted">3</span><!----><!----></span><!----></div><div class="mat-select-arrow-wrapper ng-tns-c83-151"><div class="mat-select-arrow ng-tns-c83-151"></div></div></div><!----></mat-select><span class="mat-form-field-label-wrapper ng-tns-c65-150"><label class="mat-form-field-label ng-tns-c65-150 ng-star-inserted" id="mat-form-field-label-163" for="mat-select-82" aria-owns="mat-select-82"><!----><mat-label _ngcontent-yck-c124="" class="ng-tns-c65-150 ng-star-inserted">時</mat-label><!----><span aria-hidden="true" class="mat-placeholder-required mat-form-field-required-marker ng-tns-c65-150 ng-star-inserted"> *</span><!----></label><!----></span></div><!----></div><div class="mat-form-field-underline ng-tns-c65-150 ng-star-inserted"><span class="mat-form-field-ripple ng-tns-c65-150"></span></div><!----><div class="mat-form-field-subscript-wrapper ng-tns-c65-150"><!----><div class="mat-form-field-hint-wrapper ng-tns-c65-150 ng-trigger ng-trigger-transitionMessages ng-star-inserted" style="opacity: 1; transform: translateY(0%);"><!----><!----><div class="mat-form-field-hint-spacer ng-tns-c65-150"></div></div><!----></div></div></mat-form-field></omv-form-select><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></div><div _ngcontent-yck-c53="" class="omv-form-container-item omv-flex-1 ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><omv-form-checkbox _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted ng-valid" _nghost-yck-c110=""><div _ngcontent-yck-c110="" class="omv-form-checkbox-wrapper mat-form-field omv-display-flex omv-flex-1 omv-flex-column ng-untouched ng-pristine ng-valid"><mat-checkbox _ngcontent-yck-c110="" class="mat-checkbox mat-accent ng-untouched ng-pristine ng-valid" id="mat-checkbox-50"><label class="mat-checkbox-layout" for="mat-checkbox-50-input"><span class="mat-checkbox-inner-container"><input type="checkbox" class="mat-checkbox-input cdk-visually-hidden" id="mat-checkbox-50-input" tabindex="0" aria-checked="false"><span matripple="" class="mat-ripple mat-checkbox-ripple mat-focus-indicator"><span class="mat-ripple-element mat-checkbox-persistent-ripple"></span></span><span class="mat-checkbox-frame"></span><span class="mat-checkbox-background"><svg version="1.1" focusable="false" viewBox="0 0 24 24" aria-hidden="true" class="mat-checkbox-checkmark"><path fill="none" stroke="white" d="M4.1,12.7 9,17.6 20.3,6.3" class="mat-checkbox-checkmark-path"></path></svg><span class="mat-checkbox-mixedmark"></span></span></span><span class="mat-checkbox-label"><span style="display: none;">&nbsp;</span> 毎N時 </span></label></mat-checkbox><!----><!----></div></omv-form-checkbox><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></div><!----></div><!----><!----><!----><!----><!----><!----><!----></p><!----><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><div _ngcontent-yck-c53="" class="omv-form-container omv-box-border omv-display-flex omv-flex-row omv-flex-wrap omv-gap-3 omv-align-items-stretch ng-star-inserted"><div _ngcontent-yck-c53="" class="omv-form-container-item omv-flex-1 ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><omv-form-select _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted ng-valid" _nghost-yck-c124=""><mat-form-field _ngcontent-yck-c124="" class="mat-form-field omv-flex-1 ng-tns-c65-152 mat-primary mat-form-field-type-mat-select mat-form-field-appearance-legacy mat-form-field-can-float mat-form-field-should-float mat-form-field-has-label ng-untouched ng-pristine ng-star-inserted ng-valid"><div class="mat-form-field-wrapper ng-tns-c65-152"><div class="mat-form-field-flex ng-tns-c65-152"><!----><!----><div class="mat-form-field-infix ng-tns-c65-152"><mat-select _ngcontent-yck-c124="" role="combobox" aria-autocomplete="none" aria-haspopup="true" class="mat-select ng-tns-c83-153 ng-tns-c65-152 mat-select-required mat-select-multiple ng-untouched ng-pristine ng-valid ng-star-inserted" aria-labelledby="mat-form-field-label-165 mat-select-value-85" id="mat-select-84" tabindex="0" aria-expanded="false" aria-required="true" aria-disabled="false" aria-invalid="false" required=""><div cdk-overlay-origin="" class="mat-select-trigger ng-tns-c83-153"><div class="mat-select-value ng-tns-c83-153" id="mat-select-value-85"><!----><span class="mat-select-value-text ng-tns-c83-153 ng-star-inserted"><span class="mat-select-min-line ng-tns-c83-153 ng-star-inserted">1, 10, 20, 21</span><!----><!----></span><!----></div><div class="mat-select-arrow-wrapper ng-tns-c83-153"><div class="mat-select-arrow ng-tns-c83-153"></div></div></div><!----></mat-select><span class="mat-form-field-label-wrapper ng-tns-c65-152"><label class="mat-form-field-label ng-tns-c65-152 ng-star-inserted" id="mat-form-field-label-165" for="mat-select-84" aria-owns="mat-select-84"><!----><mat-label _ngcontent-yck-c124="" class="ng-tns-c65-152 ng-star-inserted">月の日</mat-label><!----><span aria-hidden="true" class="mat-placeholder-required mat-form-field-required-marker ng-tns-c65-152 ng-star-inserted"> *</span><!----></label><!----></span></div><!----></div><div class="mat-form-field-underline ng-tns-c65-152 ng-star-inserted"><span class="mat-form-field-ripple ng-tns-c65-152"></span></div><!----><div class="mat-form-field-subscript-wrapper ng-tns-c65-152"><!----><div class="mat-form-field-hint-wrapper ng-tns-c65-152 ng-trigger ng-trigger-transitionMessages ng-star-inserted" style="opacity: 1; transform: translateY(0%);"><!----><!----><div class="mat-form-field-hint-spacer ng-tns-c65-152"></div></div><!----></div></div></mat-form-field></omv-form-select><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></div><div _ngcontent-yck-c53="" class="omv-form-container-item omv-flex-1 ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><omv-form-checkbox _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted ng-valid" _nghost-yck-c110=""><div _ngcontent-yck-c110="" class="omv-form-checkbox-wrapper mat-form-field omv-display-flex omv-flex-1 omv-flex-column ng-untouched ng-pristine ng-valid"><mat-checkbox _ngcontent-yck-c110="" class="mat-checkbox mat-accent ng-untouched ng-pristine mat-checkbox-disabled" id="mat-checkbox-51"><label class="mat-checkbox-layout" for="mat-checkbox-51-input"><span class="mat-checkbox-inner-container"><input type="checkbox" class="mat-checkbox-input cdk-visually-hidden" id="mat-checkbox-51-input" tabindex="-1" aria-checked="false" disabled=""><span matripple="" class="mat-ripple mat-checkbox-ripple mat-focus-indicator"><span class="mat-ripple-element mat-checkbox-persistent-ripple"></span></span><span class="mat-checkbox-frame"></span><span class="mat-checkbox-background"><svg version="1.1" focusable="false" viewBox="0 0 24 24" aria-hidden="true" class="mat-checkbox-checkmark"><path fill="none" stroke="white" d="M4.1,12.7 9,17.6 20.3,6.3" class="mat-checkbox-checkmark-path"></path></svg><span class="mat-checkbox-mixedmark"></span></span></span><span class="mat-checkbox-label"><span style="display: none;">&nbsp;</span> 毎月N日 </span></label></mat-checkbox><!----><!----></div></omv-form-checkbox><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></div><!----></div><!----><!----><!----><!----><!----><!----><!----></p><!----><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><omv-form-select _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted ng-valid" _nghost-yck-c124=""><mat-form-field _ngcontent-yck-c124="" class="mat-form-field omv-flex-1 ng-tns-c65-154 mat-primary mat-form-field-type-mat-select mat-form-field-appearance-legacy mat-form-field-can-float mat-form-field-should-float mat-form-field-has-label ng-untouched ng-pristine ng-star-inserted ng-valid"><div class="mat-form-field-wrapper ng-tns-c65-154"><div class="mat-form-field-flex ng-tns-c65-154"><!----><!----><div class="mat-form-field-infix ng-tns-c65-154"><mat-select _ngcontent-yck-c124="" role="combobox" aria-autocomplete="none" aria-haspopup="true" class="mat-select ng-tns-c83-155 ng-tns-c65-154 mat-select-required mat-select-multiple ng-untouched ng-pristine ng-valid ng-star-inserted" aria-labelledby="mat-form-field-label-167 mat-select-value-87" id="mat-select-86" tabindex="0" aria-expanded="false" aria-required="true" aria-disabled="false" aria-invalid="false" required=""><div cdk-overlay-origin="" class="mat-select-trigger ng-tns-c83-155"><div class="mat-select-value ng-tns-c83-155" id="mat-select-value-87"><!----><span class="mat-select-value-text ng-tns-c83-155 ng-star-inserted"><span class="mat-select-min-line ng-tns-c83-155 ng-star-inserted">*</span><!----><!----></span><!----></div><div class="mat-select-arrow-wrapper ng-tns-c83-155"><div class="mat-select-arrow ng-tns-c83-155"></div></div></div><!----></mat-select><span class="mat-form-field-label-wrapper ng-tns-c65-154"><label class="mat-form-field-label ng-tns-c65-154 ng-star-inserted" id="mat-form-field-label-167" for="mat-select-86" aria-owns="mat-select-86"><!----><mat-label _ngcontent-yck-c124="" class="ng-tns-c65-154 ng-star-inserted">月</mat-label><!----><span aria-hidden="true" class="mat-placeholder-required mat-form-field-required-marker ng-tns-c65-154 ng-star-inserted"> *</span><!----></label><!----></span></div><!----></div><div class="mat-form-field-underline ng-tns-c65-154 ng-star-inserted"><span class="mat-form-field-ripple ng-tns-c65-154"></span></div><!----><div class="mat-form-field-subscript-wrapper ng-tns-c65-154"><!----><div class="mat-form-field-hint-wrapper ng-tns-c65-154 ng-trigger ng-trigger-transitionMessages ng-star-inserted" style="opacity: 1; transform: translateY(0%);"><!----><!----><div class="mat-form-field-hint-spacer ng-tns-c65-154"></div></div><!----></div></div></mat-form-field></omv-form-select><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></p><!----><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><omv-form-select _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted ng-valid" _nghost-yck-c124=""><mat-form-field _ngcontent-yck-c124="" class="mat-form-field omv-flex-1 ng-tns-c65-156 mat-primary mat-form-field-type-mat-select mat-form-field-appearance-legacy mat-form-field-can-float mat-form-field-should-float mat-form-field-has-label ng-untouched ng-pristine ng-star-inserted ng-valid"><div class="mat-form-field-wrapper ng-tns-c65-156"><div class="mat-form-field-flex ng-tns-c65-156"><!----><!----><div class="mat-form-field-infix ng-tns-c65-156"><mat-select _ngcontent-yck-c124="" role="combobox" aria-autocomplete="none" aria-haspopup="true" class="mat-select ng-tns-c83-157 ng-tns-c65-156 mat-select-required mat-select-multiple ng-untouched ng-pristine ng-valid ng-star-inserted" aria-labelledby="mat-form-field-label-169 mat-select-value-89" id="mat-select-88" tabindex="0" aria-expanded="false" aria-required="true" aria-disabled="false" aria-invalid="false" required=""><div cdk-overlay-origin="" class="mat-select-trigger ng-tns-c83-157"><div class="mat-select-value ng-tns-c83-157" id="mat-select-value-89"><!----><span class="mat-select-value-text ng-tns-c83-157 ng-star-inserted"><span class="mat-select-min-line ng-tns-c83-157 ng-star-inserted">*</span><!----><!----></span><!----></div><div class="mat-select-arrow-wrapper ng-tns-c83-157"><div class="mat-select-arrow ng-tns-c83-157"></div></div></div><!----></mat-select><span class="mat-form-field-label-wrapper ng-tns-c65-156"><label class="mat-form-field-label ng-tns-c65-156 ng-star-inserted" id="mat-form-field-label-169" for="mat-select-88" aria-owns="mat-select-88"><!----><mat-label _ngcontent-yck-c124="" class="ng-tns-c65-156 ng-star-inserted">曜日</mat-label><!----><span aria-hidden="true" class="mat-placeholder-required mat-form-field-required-marker ng-tns-c65-156 ng-star-inserted"> *</span><!----></label><!----></span></div><!----></div><div class="mat-form-field-underline ng-tns-c65-156 ng-star-inserted"><span class="mat-form-field-ripple ng-tns-c65-156"></span></div><!----><div class="mat-form-field-subscript-wrapper ng-tns-c65-156"><!----><div class="mat-form-field-hint-wrapper ng-tns-c65-156 ng-trigger ng-trigger-transitionMessages ng-star-inserted" style="opacity: 1; transform: translateY(0%);"><!----><!----><div class="mat-form-field-hint-spacer ng-tns-c65-156"></div></div><!----></div></div></mat-form-field></omv-form-select><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></p><!----><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><omv-form-checkbox _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted ng-valid" _nghost-yck-c110=""><div _ngcontent-yck-c110="" class="omv-form-checkbox-wrapper mat-form-field omv-display-flex omv-flex-1 omv-flex-column ng-untouched ng-pristine ng-valid"><mat-checkbox _ngcontent-yck-c110="" class="mat-checkbox mat-accent ng-untouched ng-pristine ng-valid mat-checkbox-checked" id="mat-checkbox-52"><label class="mat-checkbox-layout" for="mat-checkbox-52-input"><span class="mat-checkbox-inner-container"><input type="checkbox" class="mat-checkbox-input cdk-visually-hidden" id="mat-checkbox-52-input" tabindex="0" aria-checked="true"><span matripple="" class="mat-ripple mat-checkbox-ripple mat-focus-indicator"><span class="mat-ripple-element mat-checkbox-persistent-ripple"></span></span><span class="mat-checkbox-frame"></span><span class="mat-checkbox-background"><svg version="1.1" focusable="false" viewBox="0 0 24 24" aria-hidden="true" class="mat-checkbox-checkmark"><path fill="none" stroke="white" d="M4.1,12.7 9,17.6 20.3,6.3" class="mat-checkbox-checkmark-path"></path></svg><span class="mat-checkbox-mixedmark"></span></span></span><span class="mat-checkbox-label"><span style="display: none;">&nbsp;</span> 電子メールを介してコマンドの出力を送る </span></label></mat-checkbox><!----><mat-hint _ngcontent-yck-c110="" class="mat-hint ng-star-inserted" id="mat-hint-43">Emailメッセージがコマンドの出力（あれば）とともに管理者に送られます。</mat-hint><!----></div></omv-form-checkbox><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></p><!----><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><omv-form-checkbox _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted ng-valid" _nghost-yck-c110=""><div _ngcontent-yck-c110="" class="omv-form-checkbox-wrapper mat-form-field omv-display-flex omv-flex-1 omv-flex-column ng-untouched ng-pristine ng-valid"><mat-checkbox _ngcontent-yck-c110="" class="mat-checkbox mat-accent ng-untouched ng-pristine ng-valid" id="mat-checkbox-53"><label class="mat-checkbox-layout" for="mat-checkbox-53-input"><span class="mat-checkbox-inner-container"><input type="checkbox" class="mat-checkbox-input cdk-visually-hidden" id="mat-checkbox-53-input" tabindex="0" aria-checked="false"><span matripple="" class="mat-ripple mat-checkbox-ripple mat-focus-indicator"><span class="mat-ripple-element mat-checkbox-persistent-ripple"></span></span><span class="mat-checkbox-frame"></span><span class="mat-checkbox-background"><svg version="1.1" focusable="false" viewBox="0 0 24 24" aria-hidden="true" class="mat-checkbox-checkmark"><path fill="none" stroke="white" d="M4.1,12.7 9,17.6 20.3,6.3" class="mat-checkbox-checkmark-path"></path></svg><span class="mat-checkbox-mixedmark"></span></span></span><span class="mat-checkbox-label"><span style="display: none;">&nbsp;</span> テスト実行 </span></label></mat-checkbox><!----><mat-hint _ngcontent-yck-c110="" class="mat-hint ng-star-inserted" id="mat-hint-44">設定を変更せずにテスト実行します</mat-hint><!----></div></omv-form-checkbox><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></p><!----><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><omv-form-checkbox _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted ng-valid" _nghost-yck-c110=""><div _ngcontent-yck-c110="" class="omv-form-checkbox-wrapper mat-form-field omv-display-flex omv-flex-1 omv-flex-column ng-untouched ng-pristine ng-valid"><mat-checkbox _ngcontent-yck-c110="" class="mat-checkbox mat-accent ng-untouched ng-pristine ng-valid" id="mat-checkbox-54"><label class="mat-checkbox-layout" for="mat-checkbox-54-input"><span class="mat-checkbox-inner-container"><input type="checkbox" class="mat-checkbox-input cdk-visually-hidden" id="mat-checkbox-54-input" tabindex="0" aria-checked="false"><span matripple="" class="mat-ripple mat-checkbox-ripple mat-focus-indicator"><span class="mat-ripple-element mat-checkbox-persistent-ripple"></span></span><span class="mat-checkbox-frame"></span><span class="mat-checkbox-background"><svg version="1.1" focusable="false" viewBox="0 0 24 24" aria-hidden="true" class="mat-checkbox-checkmark"><path fill="none" stroke="white" d="M4.1,12.7 9,17.6 20.3,6.3" class="mat-checkbox-checkmark-path"></path></svg><span class="mat-checkbox-mixedmark"></span></span></span><span class="mat-checkbox-label"><span style="display: none;">&nbsp;</span> 非エラーメッセージを抑制する </span></label></mat-checkbox><!----><!----></div></omv-form-checkbox><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></p><!----><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><omv-form-checkbox _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted ng-valid" _nghost-yck-c110=""><div _ngcontent-yck-c110="" class="omv-form-checkbox-wrapper mat-form-field omv-display-flex omv-flex-1 omv-flex-column ng-untouched ng-pristine ng-valid"><mat-checkbox _ngcontent-yck-c110="" class="mat-checkbox mat-accent mat-checkbox-checked ng-untouched ng-pristine ng-valid" id="mat-checkbox-55"><label class="mat-checkbox-layout" for="mat-checkbox-55-input"><span class="mat-checkbox-inner-container"><input type="checkbox" class="mat-checkbox-input cdk-visually-hidden" id="mat-checkbox-55-input" tabindex="0" aria-checked="true"><span matripple="" class="mat-ripple mat-checkbox-ripple mat-focus-indicator"><span class="mat-ripple-element mat-checkbox-persistent-ripple"></span></span><span class="mat-checkbox-frame"></span><span class="mat-checkbox-background"><svg version="1.1" focusable="false" viewBox="0 0 24 24" aria-hidden="true" class="mat-checkbox-checkmark"><path fill="none" stroke="white" d="M4.1,12.7 9,17.6 20.3,6.3" class="mat-checkbox-checkmark-path"></path></svg><span class="mat-checkbox-mixedmark"></span></span></span><span class="mat-checkbox-label"><span style="display: none;">&nbsp;</span> アーカイブモード </span></label></mat-checkbox><!----><!----></div></omv-form-checkbox><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></p><!----><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><omv-form-checkbox _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted ng-valid" _nghost-yck-c110=""><div _ngcontent-yck-c110="" class="omv-form-checkbox-wrapper mat-form-field omv-display-flex omv-flex-1 omv-flex-column ng-untouched ng-pristine ng-valid"><mat-checkbox _ngcontent-yck-c110="" class="mat-checkbox mat-accent mat-checkbox-checked ng-untouched ng-pristine ng-valid" id="mat-checkbox-56"><label class="mat-checkbox-layout" for="mat-checkbox-56-input"><span class="mat-checkbox-inner-container"><input type="checkbox" class="mat-checkbox-input cdk-visually-hidden" id="mat-checkbox-56-input" tabindex="0" aria-checked="true"><span matripple="" class="mat-ripple mat-checkbox-ripple mat-focus-indicator"><span class="mat-ripple-element mat-checkbox-persistent-ripple"></span></span><span class="mat-checkbox-frame"></span><span class="mat-checkbox-background"><svg version="1.1" focusable="false" viewBox="0 0 24 24" aria-hidden="true" class="mat-checkbox-checkmark"><path fill="none" stroke="white" d="M4.1,12.7 9,17.6 20.3,6.3" class="mat-checkbox-checkmark-path"></path></svg><span class="mat-checkbox-mixedmark"></span></span></span><span class="mat-checkbox-label"><span style="display: none;">&nbsp;</span> ディレクトリを再帰的に </span></label></mat-checkbox><!----><!----></div></omv-form-checkbox><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></p><!----><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><omv-form-checkbox _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted ng-valid" _nghost-yck-c110=""><div _ngcontent-yck-c110="" class="omv-form-checkbox-wrapper mat-form-field omv-display-flex omv-flex-1 omv-flex-column ng-untouched ng-pristine ng-valid"><mat-checkbox _ngcontent-yck-c110="" class="mat-checkbox mat-accent mat-checkbox-checked ng-untouched ng-pristine ng-valid" id="mat-checkbox-57"><label class="mat-checkbox-layout" for="mat-checkbox-57-input"><span class="mat-checkbox-inner-container"><input type="checkbox" class="mat-checkbox-input cdk-visually-hidden" id="mat-checkbox-57-input" tabindex="0" aria-checked="true"><span matripple="" class="mat-ripple mat-checkbox-ripple mat-focus-indicator"><span class="mat-ripple-element mat-checkbox-persistent-ripple"></span></span><span class="mat-checkbox-frame"></span><span class="mat-checkbox-background"><svg version="1.1" focusable="false" viewBox="0 0 24 24" aria-hidden="true" class="mat-checkbox-checkmark"><path fill="none" stroke="white" d="M4.1,12.7 9,17.6 20.3,6.3" class="mat-checkbox-checkmark-path"></path></svg><span class="mat-checkbox-mixedmark"></span></span></span><span class="mat-checkbox-label"><span style="display: none;">&nbsp;</span> パーミッションを保存 </span></label></mat-checkbox><!----><mat-hint _ngcontent-yck-c110="" class="mat-hint ng-star-inserted" id="mat-hint-45">元のアクセス権と同じになるように先のアクセス権を設定します。</mat-hint><!----></div></omv-form-checkbox><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></p><!----><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><omv-form-checkbox _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted ng-valid" _nghost-yck-c110=""><div _ngcontent-yck-c110="" class="omv-form-checkbox-wrapper mat-form-field omv-display-flex omv-flex-1 omv-flex-column ng-untouched ng-pristine ng-valid"><mat-checkbox _ngcontent-yck-c110="" class="mat-checkbox mat-accent mat-checkbox-checked ng-untouched ng-pristine ng-valid" id="mat-checkbox-58"><label class="mat-checkbox-layout" for="mat-checkbox-58-input"><span class="mat-checkbox-inner-container"><input type="checkbox" class="mat-checkbox-input cdk-visually-hidden" id="mat-checkbox-58-input" tabindex="0" aria-checked="true"><span matripple="" class="mat-ripple mat-checkbox-ripple mat-focus-indicator"><span class="mat-ripple-element mat-checkbox-persistent-ripple"></span></span><span class="mat-checkbox-frame"></span><span class="mat-checkbox-background"><svg version="1.1" focusable="false" viewBox="0 0 24 24" aria-hidden="true" class="mat-checkbox-checkmark"><path fill="none" stroke="white" d="M4.1,12.7 9,17.6 20.3,6.3" class="mat-checkbox-checkmark-path"></path></svg><span class="mat-checkbox-mixedmark"></span></span></span><span class="mat-checkbox-label"><span style="display: none;">&nbsp;</span> 修正時刻を保存 </span></label></mat-checkbox><!----><mat-hint _ngcontent-yck-c110="" class="mat-hint ng-star-inserted" id="mat-hint-46">変更時間をファイルとともに転送し、リモートシステムで更新します。</mat-hint><!----></div></omv-form-checkbox><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></p><!----><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><omv-form-checkbox _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted ng-valid" _nghost-yck-c110=""><div _ngcontent-yck-c110="" class="omv-form-checkbox-wrapper mat-form-field omv-display-flex omv-flex-1 omv-flex-column ng-untouched ng-pristine ng-valid"><mat-checkbox _ngcontent-yck-c110="" class="mat-checkbox mat-accent mat-checkbox-checked ng-untouched ng-pristine ng-valid" id="mat-checkbox-59"><label class="mat-checkbox-layout" for="mat-checkbox-59-input"><span class="mat-checkbox-inner-container"><input type="checkbox" class="mat-checkbox-input cdk-visually-hidden" id="mat-checkbox-59-input" tabindex="0" aria-checked="true"><span matripple="" class="mat-ripple mat-checkbox-ripple mat-focus-indicator"><span class="mat-ripple-element mat-checkbox-persistent-ripple"></span></span><span class="mat-checkbox-frame"></span><span class="mat-checkbox-background"><svg version="1.1" focusable="false" viewBox="0 0 24 24" aria-hidden="true" class="mat-checkbox-checkmark"><path fill="none" stroke="white" d="M4.1,12.7 9,17.6 20.3,6.3" class="mat-checkbox-checkmark-path"></path></svg><span class="mat-checkbox-mixedmark"></span></span></span><span class="mat-checkbox-label"><span style="display: none;">&nbsp;</span> グループを維持 </span></label></mat-checkbox><!----><mat-hint _ngcontent-yck-c110="" class="mat-hint ng-star-inserted" id="mat-hint-47">宛先ファイルのグループを元のファイルと同じになるように設定します。</mat-hint><!----></div></omv-form-checkbox><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></p><!----><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><omv-form-checkbox _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted ng-valid" _nghost-yck-c110=""><div _ngcontent-yck-c110="" class="omv-form-checkbox-wrapper mat-form-field omv-display-flex omv-flex-1 omv-flex-column ng-untouched ng-pristine ng-valid"><mat-checkbox _ngcontent-yck-c110="" class="mat-checkbox mat-accent mat-checkbox-checked ng-untouched ng-pristine ng-valid" id="mat-checkbox-60"><label class="mat-checkbox-layout" for="mat-checkbox-60-input"><span class="mat-checkbox-inner-container"><input type="checkbox" class="mat-checkbox-input cdk-visually-hidden" id="mat-checkbox-60-input" tabindex="0" aria-checked="true"><span matripple="" class="mat-ripple mat-checkbox-ripple mat-focus-indicator"><span class="mat-ripple-element mat-checkbox-persistent-ripple"></span></span><span class="mat-checkbox-frame"></span><span class="mat-checkbox-background"><svg version="1.1" focusable="false" viewBox="0 0 24 24" aria-hidden="true" class="mat-checkbox-checkmark"><path fill="none" stroke="white" d="M4.1,12.7 9,17.6 20.3,6.3" class="mat-checkbox-checkmark-path"></path></svg><span class="mat-checkbox-mixedmark"></span></span></span><span class="mat-checkbox-label"><span style="display: none;">&nbsp;</span> オーナーを維持 </span></label></mat-checkbox><!----><mat-hint _ngcontent-yck-c110="" class="mat-hint ng-star-inserted" id="mat-hint-48">受信側のrsyncがスーパーユーザーとして実行されている場合のみ、送信先ファイルの所有者を送信元ファイルと同じに設定します。</mat-hint><!----></div></omv-form-checkbox><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></p><!----><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><omv-form-checkbox _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted ng-valid" _nghost-yck-c110=""><div _ngcontent-yck-c110="" class="omv-form-checkbox-wrapper mat-form-field omv-display-flex omv-flex-1 omv-flex-column ng-untouched ng-pristine ng-valid"><mat-checkbox _ngcontent-yck-c110="" class="mat-checkbox mat-accent ng-untouched ng-pristine ng-valid" id="mat-checkbox-61"><label class="mat-checkbox-layout" for="mat-checkbox-61-input"><span class="mat-checkbox-inner-container"><input type="checkbox" class="mat-checkbox-input cdk-visually-hidden" id="mat-checkbox-61-input" tabindex="0" aria-checked="false"><span matripple="" class="mat-ripple mat-checkbox-ripple mat-focus-indicator"><span class="mat-ripple-element mat-checkbox-persistent-ripple"></span></span><span class="mat-checkbox-frame"></span><span class="mat-checkbox-background"><svg version="1.1" focusable="false" viewBox="0 0 24 24" aria-hidden="true" class="mat-checkbox-checkmark"><path fill="none" stroke="white" d="M4.1,12.7 9,17.6 20.3,6.3" class="mat-checkbox-checkmark-path"></path></svg><span class="mat-checkbox-mixedmark"></span></span></span><span class="mat-checkbox-label"><span style="display: none;">&nbsp;</span> 圧縮 </span></label></mat-checkbox><!----><mat-hint _ngcontent-yck-c110="" class="mat-hint ng-star-inserted" id="mat-hint-49">転送中にファイルデータを圧縮します。</mat-hint><!----></div></omv-form-checkbox><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></p><!----><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><omv-form-checkbox _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted ng-valid" _nghost-yck-c110=""><div _ngcontent-yck-c110="" class="omv-form-checkbox-wrapper mat-form-field omv-display-flex omv-flex-1 omv-flex-column ng-untouched ng-pristine ng-valid"><mat-checkbox _ngcontent-yck-c110="" class="mat-checkbox mat-accent ng-untouched ng-pristine ng-valid" id="mat-checkbox-62"><label class="mat-checkbox-layout" for="mat-checkbox-62-input"><span class="mat-checkbox-inner-container"><input type="checkbox" class="mat-checkbox-input cdk-visually-hidden" id="mat-checkbox-62-input" tabindex="0" aria-checked="false"><span matripple="" class="mat-ripple mat-checkbox-ripple mat-focus-indicator"><span class="mat-ripple-element mat-checkbox-persistent-ripple"></span></span><span class="mat-checkbox-frame"></span><span class="mat-checkbox-background"><svg version="1.1" focusable="false" viewBox="0 0 24 24" aria-hidden="true" class="mat-checkbox-checkmark"><path fill="none" stroke="white" d="M4.1,12.7 9,17.6 20.3,6.3" class="mat-checkbox-checkmark-path"></path></svg><span class="mat-checkbox-mixedmark"></span></span></span><span class="mat-checkbox-label"><span style="display: none;">&nbsp;</span> ACLを保存 </span></label></mat-checkbox><!----><mat-hint _ngcontent-yck-c110="" class="mat-hint ng-star-inserted" id="mat-hint-50">元のACLと同じになるように先のACLを更新します。</mat-hint><!----></div></omv-form-checkbox><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></p><!----><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><omv-form-checkbox _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted ng-valid" _nghost-yck-c110=""><div _ngcontent-yck-c110="" class="omv-form-checkbox-wrapper mat-form-field omv-display-flex omv-flex-1 omv-flex-column ng-untouched ng-pristine ng-valid"><mat-checkbox _ngcontent-yck-c110="" class="mat-checkbox mat-accent ng-untouched ng-pristine ng-valid" id="mat-checkbox-63"><label class="mat-checkbox-layout" for="mat-checkbox-63-input"><span class="mat-checkbox-inner-container"><input type="checkbox" class="mat-checkbox-input cdk-visually-hidden" id="mat-checkbox-63-input" tabindex="0" aria-checked="false"><span matripple="" class="mat-ripple mat-checkbox-ripple mat-focus-indicator"><span class="mat-ripple-element mat-checkbox-persistent-ripple"></span></span><span class="mat-checkbox-frame"></span><span class="mat-checkbox-background"><svg version="1.1" focusable="false" viewBox="0 0 24 24" aria-hidden="true" class="mat-checkbox-checkmark"><path fill="none" stroke="white" d="M4.1,12.7 9,17.6 20.3,6.3" class="mat-checkbox-checkmark-path"></path></svg><span class="mat-checkbox-mixedmark"></span></span></span><span class="mat-checkbox-label"><span style="display: none;">&nbsp;</span> 拡張属性を保存 </span></label></mat-checkbox><!----><mat-hint _ngcontent-yck-c110="" class="mat-hint ng-star-inserted" id="mat-hint-51">元の拡張属性と同じになるように先の拡張属性を更新します。</mat-hint><!----></div></omv-form-checkbox><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></p><!----><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><omv-form-checkbox _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted ng-valid" _nghost-yck-c110=""><div _ngcontent-yck-c110="" class="omv-form-checkbox-wrapper mat-form-field omv-display-flex omv-flex-1 omv-flex-column ng-untouched ng-pristine ng-valid"><mat-checkbox _ngcontent-yck-c110="" class="mat-checkbox mat-accent ng-untouched ng-pristine ng-valid" id="mat-checkbox-64"><label class="mat-checkbox-layout" for="mat-checkbox-64-input"><span class="mat-checkbox-inner-container"><input type="checkbox" class="mat-checkbox-input cdk-visually-hidden" id="mat-checkbox-64-input" tabindex="0" aria-checked="false"><span matripple="" class="mat-ripple mat-checkbox-ripple mat-focus-indicator"><span class="mat-ripple-element mat-checkbox-persistent-ripple"></span></span><span class="mat-checkbox-frame"></span><span class="mat-checkbox-background"><svg version="1.1" focusable="false" viewBox="0 0 24 24" aria-hidden="true" class="mat-checkbox-checkmark"><path fill="none" stroke="white" d="M4.1,12.7 9,17.6 20.3,6.3" class="mat-checkbox-checkmark-path"></path></svg><span class="mat-checkbox-mixedmark"></span></span></span><span class="mat-checkbox-label"><span style="display: none;">&nbsp;</span> 部分的に転送されたファイルを保持する </span></label></mat-checkbox><!----><mat-hint _ngcontent-yck-c110="" class="mat-hint ng-star-inserted" id="mat-hint-52">部分的に転送されたファイルを保持する場合はこのオプションを有効にします。それ以外の場合は転送が中断された場合、ファイルは削除されます。</mat-hint><!----></div></omv-form-checkbox><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></p><!----><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><!----><!----><!----><!----><!----><omv-form-checkbox _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted ng-valid" _nghost-yck-c110=""><div _ngcontent-yck-c110="" class="omv-form-checkbox-wrapper mat-form-field omv-display-flex omv-flex-1 omv-flex-column ng-untouched ng-pristine ng-valid"><mat-checkbox _ngcontent-yck-c110="" class="mat-checkbox mat-accent ng-untouched ng-pristine ng-valid mat-checkbox-checked" id="mat-checkbox-65"><label class="mat-checkbox-layout" for="mat-checkbox-65-input"><span class="mat-checkbox-inner-container"><input type="checkbox" class="mat-checkbox-input cdk-visually-hidden" id="mat-checkbox-65-input" tabindex="0" aria-checked="true"><span matripple="" class="mat-ripple mat-checkbox-ripple mat-focus-indicator"><span class="mat-ripple-element mat-checkbox-persistent-ripple"></span></span><span class="mat-checkbox-frame"></span><span class="mat-checkbox-background"><svg version="1.1" focusable="false" viewBox="0 0 24 24" aria-hidden="true" class="mat-checkbox-checkmark"><path fill="none" stroke="white" d="M4.1,12.7 9,17.6 20.3,6.3" class="mat-checkbox-checkmark-path"></path></svg><span class="mat-checkbox-mixedmark"></span></span></span><span class="mat-checkbox-label"><span style="display: none;">&nbsp;</span> 削除 </span></label></mat-checkbox><!----><mat-hint _ngcontent-yck-c110="" class="mat-hint ng-star-inserted" id="mat-hint-53">送信側に存在しないファイルは受信側で削除されます。</mat-hint><!----></div></omv-form-checkbox><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></p><!----><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><omv-form-text-input _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted ng-valid" _nghost-yck-c131=""><mat-form-field _ngcontent-yck-c131="" class="mat-form-field omv-flex-1 ng-tns-c65-158 mat-primary mat-form-field-type-mat-input mat-form-field-appearance-legacy mat-form-field-can-float mat-form-field-should-float mat-form-field-has-label ng-untouched ng-pristine ng-star-inserted ng-valid"><div class="mat-form-field-wrapper ng-tns-c65-158"><div class="mat-form-field-flex ng-tns-c65-158"><!----><!----><div class="mat-form-field-infix ng-tns-c65-158"><input _ngcontent-yck-c131="" matinput="" type="text" class="mat-autocomplete-trigger mat-input-element mat-form-field-autofill-control omv-text-truncate ng-tns-c65-158 ng-untouched ng-pristine ng-valid cdk-text-field-autofill-monitored" autocapitalize="none" aria-describedby="mat-hint-54" id="mat-input-35" aria-invalid="false" aria-required="false"><!----><mat-autocomplete _ngcontent-yck-c131="" autoactivefirstoption="" class="mat-autocomplete ng-tns-c65-158"><!----></mat-autocomplete><span class="mat-form-field-label-wrapper ng-tns-c65-158"><label class="mat-form-field-label ng-tns-c65-158 ng-star-inserted" id="mat-form-field-label-171" for="mat-input-35" aria-owns="mat-input-35"><!----><mat-label _ngcontent-yck-c131="" class="ng-tns-c65-158 ng-star-inserted">追加オプション</mat-label><!----><!----></label><!----></span></div><!----></div><div class="mat-form-field-underline ng-tns-c65-158 ng-star-inserted"><span class="mat-form-field-ripple ng-tns-c65-158"></span></div><!----><div class="mat-form-field-subscript-wrapper ng-tns-c65-158"><!----><div class="mat-form-field-hint-wrapper ng-tns-c65-158 ng-trigger ng-trigger-transitionMessages ng-star-inserted" style="opacity: 1; transform: translateY(0%);"><!----><mat-hint _ngcontent-yck-c131="" class="mat-hint ng-tns-c65-158 ng-star-inserted" id="mat-hint-54" style="">Please check the <a href="https://download.samba.org/pub/rsync/rsync.1" target="_blank">manual page</a> for more details.</mat-hint><!----><div class="mat-form-field-hint-spacer ng-tns-c65-158"></div></div><!----></div></div></mat-form-field></omv-form-text-input><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></p><!----><p _ngcontent-yck-c53="" class="ng-star-inserted"><!----><!----><!----><omv-form-tag-input _ngcontent-yck-c53="" class="omv-display-flex ng-untouched ng-pristine ng-star-inserted ng-valid" _nghost-yck-c130=""><mat-form-field _ngcontent-yck-c130="" class="mat-form-field omv-flex-1 ng-tns-c65-159 mat-primary mat-form-field-type-tag-input mat-form-field-appearance-legacy mat-form-field-can-float mat-form-field-should-float mat-form-field-has-label ng-untouched ng-pristine ng-star-inserted ng-valid"><div class="mat-form-field-wrapper ng-tns-c65-159"><div class="mat-form-field-flex ng-tns-c65-159"><!----><!----><div class="mat-form-field-infix ng-tns-c65-159"><mat-form-tag-input _ngcontent-yck-c130="" _nghost-yck-c129="" class="ng-tns-c65-159 ng-untouched ng-pristine ng-valid"><mat-chip-list _ngcontent-yck-c129="" class="mat-chip-list" data-mat-chip-input="mat-chip-list-input-4" id="mat-chip-list-16" tabindex="-1" aria-disabled="false" aria-invalid="false" aria-multiselectable="false" aria-orientation="horizontal"><div class="mat-chip-list-wrapper"><!----><input _ngcontent-yck-c129="" matchipinputaddonblur="" class="mat-chip-input mat-input-element ng-star-inserted" id="mat-chip-list-input-4"><!----></div></mat-chip-list></mat-form-tag-input><span class="mat-form-field-label-wrapper ng-tns-c65-159"><label class="mat-form-field-label ng-tns-c65-159 ng-star-inserted" id="mat-form-field-label-173" for="mat-form-tag-input-5" aria-owns="mat-form-tag-input-5"><!----><mat-label _ngcontent-yck-c130="" class="ng-tns-c65-159 ng-star-inserted">Tags</mat-label><!----><!----></label><!----></span></div><!----></div><div class="mat-form-field-underline ng-tns-c65-159 ng-star-inserted"><span class="mat-form-field-ripple ng-tns-c65-159"></span></div><!----><div class="mat-form-field-subscript-wrapper ng-tns-c65-159"><!----><div class="mat-form-field-hint-wrapper ng-tns-c65-159 ng-trigger ng-trigger-transitionMessages ng-star-inserted" style="opacity: 1; transform: translateY(0%);"><!----><!----><div class="mat-form-field-hint-spacer ng-tns-c65-159"></div></div><!----></div></div></mat-form-field></omv-form-tag-input><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----><!----></p><!----><!----></form><!----></omv-intuition-form></mat-card-content>

### 🤖 Assistant (2025-11-20 23:33)

 画面設定を確認しました。現在の設定は：

## 現在のスケジュール設定
- **分**: 10
- **時**: 3
- **月の日**: 1, 10, 20, 21
- **月**: * (毎月)
- **曜日**: * (全曜日)

→ **毎月1日、10日、20日、21日の午前3時10分**に実行

## メール通知の設定
✅ **「電子メールを介してコマンドの出力を送る」がON**になっています

これが原因で、メールシステムがないため通知が届かない状態です。

## 推奨される変更

### 1. 毎日実行に変更する場合

**「月の日」**のドロップダウンをクリックして：
- 現在の「1, 10, 20, 21」を解除
- **「*」（アスタリスク）を選択**

これで**毎日午前3時10分**に実行されます。

### 2. メール通知をオフにする（推奨）

メールシステムが設定されていないので：
- ☑ **「電子メールを介してコマンドの出力を送る」のチェックを外す**

### 3. 設定を保存

1. 画面下部の**「保存」**ボタンをクリック
2. 画面上部に黄色い通知バーが表示されたら**「適用」**をクリック

## 変更後の確認

```bash
# cron設定が更新されたか確認
sudo cat /etc/cron.d/nas-server-rsync

# 次回実行予定を確認（毎日3:10になっているはず）
```

毎日実行とメール通知オフに変更しますか？

### 👤 Human (2025-11-20 23:34)

いやいや、openmediumvaultの通知設定しているから手動実行のメールは届いたよ？

### 🤖 Assistant (2025-11-20 23:34)

 あ、失礼しました！OpenMediaVaultのメール通知設定が正しくされているんですね。

それなら、cronの自動実行時のメールも届くはずです。確認方法：

## 次回の自動実行でメールが届くか確認

次回の実行予定：**2025年12月1日 午前3:10**

12月1日の午前3時以降に、OpenMediaVaultの通知設定で指定したメールアドレスに実行結果が届きます。

## すぐに確認したい場合

スケジュールを一時的に変更して、数分後に実行させる：

1. 現在時刻を確認（例：15:30）
2. OpenMediaVault管理画面で編集：
   - **分**: 35（現在+5分後）
   - **時**: 15（現在の時刻）
   - **月の日**: `*`（今日も実行されるように）
3. 保存→適用
4. 5分後にメールが届くか確認

## 確認後

メールが届いたら、スケジュールを元に戻すか、希望の頻度（毎日など）に設定し直してください。

cronは正常に動いているので、スケジュール通りに自動実行され、メール通知も届くはずです！

### 👤 Human (2025-11-20 23:47)

パッケージ情報
nas-server-anacron 7.0
anacron plugin for OpenMediaVault.
セクション: Utilities
メンテナ: OpenMediaVault Plugin Developers <plugins@omv-extras.org>
ホームページ: http://omv-extras.org/
リポジトリ: /
サイズ: 14.14 KiB
nas-server-wakealarm 7.0
wakealarm plugin for OpenMediaVault.
Schedule times to wake machine using wakealarm
セクション: Utilities
メンテナ: OpenMediaVault Plugin Developers <plugins@omv-extras.org>
リポジトリ: /
サイズ: 13.83 KiB


これは未インストールです。cronに影響なし？

### 🤖 Assistant (2025-11-20 23:47)

 はい、**cronには影響ありません**。

## これらのプラグインについて

### nas-server-anacron
- **anacron**は、電源が切れていた時間帯のcronジョブを後で実行するためのツール
- サーバーが24時間稼働していない場合に便利
- 例：午前3時に実行予定だったが電源OFFだった → 次回起動時に実行

### nas-server-wakealarm
- スケジュールに合わせて自動的にマシンを起動する機能
- 例：毎日午前2時55分に自動起動 → 午前3時のバックアップを実行

## 現在の状況では不要

OpenMediaVaultサーバーが**24時間稼働している**なら、これらのプラグインは不要です。

通常の**cron**で十分機能しています：
- ✅ cronサービス: 正常動作
- ✅ rsyncジョブ: 正しく登録済み
- ✅ 手動実行: 成功
- ✅ メール通知: 設定済み

## インストールを検討すべき場合

以下の場合のみインストールを検討：
1. **サーバーを定期的にシャットダウンする**（電気代節約など）
   → anacronをインストール
2. **バックアップ時だけ自動起動したい**
   → wakealarmをインストール

24時間稼働なら、現在の設定のままで問題ありません。


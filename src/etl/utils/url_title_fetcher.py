"""
URL からHTMLタイトルを取得するモジュール

標準ライブラリのみを使用し、外部依存を最小化。
"""

import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from typing import TypedDict
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


class URLReference(TypedDict):
    """URL参照情報"""

    url: str
    title: str | None


class TitleParser(HTMLParser):
    """<title>タグを抽出するパーサー"""

    def __init__(self):
        super().__init__()
        self.in_title = False
        self.title = ""

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


class URLTitleFetcher:
    """
    URLからHTMLタイトルを取得

    - タイムアウト: 5秒/URL
    - 並列処理: 最大3並列
    - キャッシング: セッション内で同一URL重複取得を防ぐ
    """

    DEFAULT_TIMEOUT = 5  # 秒
    MAX_WORKERS = 3
    USER_AGENT = "Mozilla/5.0 (compatible; ObsidianETL/1.0)"

    def __init__(self, timeout: int = DEFAULT_TIMEOUT, max_workers: int = MAX_WORKERS):
        """
        Args:
            timeout: HTTP リクエストタイムアウト（秒）
            max_workers: 並列処理の最大ワーカー数
        """
        self.timeout = timeout
        self.max_workers = max_workers
        self._cache: dict[str, str | None] = {}

    def fetch_title(self, url: str) -> str | None:
        """
        単一URLからタイトルを取得

        Args:
            url: 取得対象のURL

        Returns:
            HTMLタイトル（取得失敗時は None）
        """
        # キャッシュチェック
        if url in self._cache:
            logger.debug(f"キャッシュヒット: {url}")
            return self._cache[url]

        try:
            # HTTP GET リクエスト
            req = Request(url, headers={"User-Agent": self.USER_AGENT})
            with urlopen(req, timeout=self.timeout) as response:
                # Content-Type チェック（HTML以外はスキップ）
                content_type = response.headers.get("Content-Type", "")
                if "text/html" not in content_type.lower():
                    logger.debug(f"HTML以外のコンテンツ: {url} ({content_type})")
                    self._cache[url] = None
                    return None

                # HTML を読み込み（最初の 10KB のみ）
                html = response.read(10240).decode("utf-8", errors="ignore")

            # <title> タグを抽出
            parser = TitleParser()
            parser.feed(html)
            title = parser.title.strip()

            if title:
                # 空白を正規化
                title = re.sub(r"\s+", " ", title)
                logger.debug(f"タイトル取得成功: {url} → {title}")
                self._cache[url] = title
                return title
            else:
                logger.debug(f"<title>タグが空: {url}")
                self._cache[url] = None
                return None

        except (HTTPError, URLError) as e:
            logger.debug(f"HTTP エラー: {url} → {e}")
            self._cache[url] = None
            return None
        except Exception as e:
            logger.debug(f"予期しないエラー: {url} → {e}")
            self._cache[url] = None
            return None

    def fetch_titles(self, urls: list[str]) -> list[URLReference]:
        """
        複数URLから並列でタイトルを取得

        Args:
            urls: 取得対象のURLリスト

        Returns:
            URLReference のリスト
        """
        if not urls:
            return []

        results: dict[str, str | None] = {}

        # 並列処理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {executor.submit(self.fetch_title, url): url for url in urls}

            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    title = future.result()
                    results[url] = title
                except Exception as e:
                    logger.error(f"タイトル取得失敗: {url} → {e}")
                    results[url] = None

        # URLReference 形式に変換（元の順序を維持）
        return [{"url": url, "title": results.get(url)} for url in urls]

    def clear_cache(self):
        """キャッシュをクリア"""
        self._cache.clear()

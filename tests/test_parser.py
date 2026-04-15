from __future__ import annotations

import unittest

from curly_agent.scraper import parse_homepage, select_candidate


HOME_HTML = """
<div class="page-heading"><span class="page-heading__ttl-main">CURLY'S NEWS</span></div>
<div class="articles__container">
  <article class="articles__unit"><a class="newslead" href="https://curlycollection.jp/2026/04/93890/">
    <div class="articles__thumb" data-original="https://curlycollection.jp/wp-content/uploads/2026/04/a.jpg"></div>
    <h2 class="articles__ttl">マスコットチャーム付き♡NEWメッシュバッグ</h2>
    <p class="articles__date"><time datetime="2026-04-14">2026.04.14</time></p>
    <div class="articles__desc newsdetail">説明テキスト</div>
  </a></article>
</div>
<div class="page-heading"><span class="page-heading__ttl-main">NEW ARRIVALS</span></div>
<div class="item-list__container">
  <div class="item"><div class="item__container"><a href="https://curlycollection.jp/shop/products/detail/85797">
    <span class="item__thumb"><span class="item__thumb-img" data-original="/shop/upload/save_image/0413094842_69dc3d6a7c915.jpg"></span></span>
    <span class="item__name">着ぐるみマスコットチャーム☆ハローキティいちごちゃん</span>
    <span class="item__price price"><span class="icon-ani--new">NEW</span> ¥ 2,970</span>
    <span class="item__id">cha4759</span>
  </a></div></div>
</div>
"""


class ParserTests(unittest.TestCase):
    def test_parse_homepage_finds_news_and_arrivals(self) -> None:
        candidates = parse_homepage(HOME_HTML, "https://curlycollection.jp/")
        self.assertEqual(len(candidates), 2)
        self.assertEqual(candidates[0].source_section, "news")
        self.assertEqual(candidates[1].source_section, "new_arrivals")
        self.assertTrue(candidates[1].is_new)

    def test_selection_prefers_arrivals(self) -> None:
        candidates = parse_homepage(HOME_HTML, "https://curlycollection.jp/")
        selection = select_candidate(candidates)
        self.assertEqual(selection.item.source_section, "new_arrivals")
        self.assertIn("综合得分", selection.reason)


if __name__ == "__main__":
    unittest.main()

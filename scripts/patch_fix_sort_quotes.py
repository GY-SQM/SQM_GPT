# -*- coding: utf-8 -*-
"""
patch_fix_sort_quotes.py
========================
patch_embed_lot_panel.py / patch_wh_dash_lot_panel.py 가 생성한
onclick 버튼의 인용부호 오류 수정.

  문제: onclick="window.fn('asc')" → 싱글쿼트가 JS 문자열 구분자와 충돌
  수정: onclick="window.fn(\'asc\')" → 백슬래시 이스케이프
"""
import pathlib, sys, shutil, datetime

STAMP = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

FIXES = [
    (
        pathlib.Path(__file__).parent.parent / 'frontend' / 'js' / 'dashboard-warehouse-embed.js',
        [
            (
                "'<button onclick=\"window._whEmbedSortLots('asc')\" '",
                "'<button onclick=\"window._whEmbedSortLots(\\'asc\\')\" '"
            ),
            (
                "'<button onclick=\"window._whEmbedSortLots('desc')\" '",
                "'<button onclick=\"window._whEmbedSortLots(\\'desc\\')\" '"
            ),
        ]
    ),
    (
        pathlib.Path(__file__).parent.parent / 'frontend' / 'js' / 'sqm-warehouse-dashboard.js',
        [
            (
                "'<button onclick=\"window._whdDashSortLots('asc')\" '",
                "'<button onclick=\"window._whdDashSortLots(\\'asc\\')\" '"
            ),
            (
                "'<button onclick=\"window._whdDashSortLots('desc')\" '",
                "'<button onclick=\"window._whdDashSortLots(\\'desc\\')\" '"
            ),
        ]
    ),
]

for target, replacements in FIXES:
    src = target.read_text(encoding='utf-8')
    changed = False
    for old, new in replacements:
        if old not in src:
            print(f'  WARN: 패턴 없음 (이미 수정됐거나 불일치): {old[:60]}')
            continue
        src = src.replace(old, new, 1)
        print(f'  OK: {target.name} → {old[:55]}...')
        changed = True
    if changed:
        bak = target.with_suffix('.js.bak_fixquote_' + STAMP)
        shutil.copy2(target, bak)
        target.write_text(src, encoding='utf-8')
        print(f'  저장: {target.name}  ({src.count(chr(10)) + 1} 줄)')

print('DONE.')

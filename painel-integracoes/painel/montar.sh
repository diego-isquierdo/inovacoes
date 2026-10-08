#!/bin/sh
# Monta painel_v1.html (publicavel) e painel_teste.html (com gancho __TEST__) a partir de partes/
cd "$(dirname "$0")"
cat partes/a_head.html partes/b_core.js partes/c_views.js partes/d_charts.js partes/e_tail.js > painel_teste.html
grep -v "window.__TEST__=" painel_teste.html > painel_v1.html

\echo '(1) VNINDEX value/volume ratio outside 100..1e7 or null volume (expect 0 rows)'
SELECT trading_date, value, v, value / NULLIF(v,0) AS ratio FROM index_1d
WHERE index_code='VNINDEX' AND (value / NULLIF(v,0) NOT BETWEEN 100 AND 1e7 OR v IS NULL) ORDER BY 1 LIMIT 20;
\echo '(2) weekend crawl_sessions rows (expect 0 rows)'
SELECT * FROM crawl_sessions WHERE extract(isodow FROM trading_date) > 5;
\echo '(3a) last crawl_runs row'
SELECT * FROM crawl_runs ORDER BY 1 DESC LIMIT 1;
\echo '(3b) last 3 crawl_sessions per feed'
SELECT * FROM (SELECT *, row_number() OVER (PARTITION BY feed ORDER BY trading_date DESC) AS rn FROM crawl_sessions) t WHERE rn <= 3 ORDER BY feed, trading_date DESC;

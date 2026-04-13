-- =====================================
-- VEHICLE: 500 rows
-- =====================================
INSERT INTO VEHICLE (plate_number, vehicle_type, capacity)
SELECT
  (3000000 + ((i * 7919) % 6000000))::text AS plate_number,
  (ARRAY[
    'Minibus',
    'Tour Bus',
    'Van',
    'Accessible Van',
    'Shuttle Bus',
    'Coach'
  ])[((i - 1) % 6) + 1] AS vehicle_type,
  (ARRAY[
    14, 16, 18, 20, 24, 28, 32, 40, 52
  ])[((i - 1) % 9) + 1] AS capacity
FROM generate_series(1, 500) AS g(i);


-- =====================================
-- REGION: 500 rows
-- =====================================
INSERT INTO REGION (region_id, regio_name, terrain_type, description)
SELECT
  i,
  prefix || ' ' || core || ' ' || suffix AS regio_name,
  (ARRAY[
    'Mountain','Urban','Coastal','Rural','Desert'
  ])[((i - 1) % 5) + 1] AS terrain_type,
  (ARRAY[
    'אזור תפעולי להסעות תיירות ונופש',
    'אזור הכולל אתרי טבע, תרבות ופנאי',
    'אזור שירות למסלולי מבקרים ואתרי מורשת',
    'אזור פעילות להסעות קבוצות ומטיילים',
    'אזור הפעלה למסלולי תיירות ואטרקציות'
  ])[((i - 1) % 5) + 1] AS description
FROM (
  SELECT
    i,
    (ARRAY[
      'גליל','כרמל','שרון','נגב','שפלה',
      'בקעה','חוף','הר','עמק','מישור'
    ])[((i - 1) % 10) + 1] AS prefix,
    (ARRAY[
      'המערבי','המזרחי','העליון','התחתון','המרכזי',
      'הצפוני','הדרומי','הירוק','הכפרי','העירוני'
    ])[(((i - 1) / 10) % 10) + 1] AS core,
    (ARRAY[
      'התיירותי','הנופי','הקהילתי','ההיסטורי','הפתוח'
    ])[(((i - 1) / 100) % 5) + 1] AS suffix
  FROM generate_series(1, 500) AS g(i)
) q;


-- =====================================
-- SITE: 20000 rows
-- 20 * 10 * 10 * 10 = 20000 unique names
-- =====================================
INSERT INTO SITE (site_name, site_type, address)
SELECT
  city_name || ' ' || site_type || ' ' || theme_word || ' ' || descriptor_word AS site_name,
  site_type,
  street_name || ', ' || city_name AS address
FROM (
  SELECT
    i,
    (ARRAY[
      'ירושלים','תל אביב','חיפה','נצרת','עכו',
      'טבריה','צפת','אילת','אשדוד','אשקלון',
      'נתניה','הרצליה','רעננה','כפר סבא','מודיעין',
      'באר שבע','חולון','בת ים','רמת גן','פתח תקווה'
    ])[((i - 1) % 20) + 1] AS city_name,
    (ARRAY[
      'מוזיאון','גן לאומי','טיילת','חוף','פארק',
      'מרכז מבקרים','אתר מורשת','שמורת טבע','מרכז תרבות','כפר נופש'
    ])[(((i - 1) / 20) % 10) + 1] AS site_type,
    (ARRAY[
      'השלום','הגליל','הכרמל','הים','המעיין',
      'האופק','החורש','הנמל','הפסגה','הזהב'
    ])[(((i - 1) / 200) % 10) + 1] AS theme_word,
    (ARRAY[
      'העתיק','המרכזי','הירוק','הפתוח','החופי',
      'הצפוני','הדרומי','הקהילתי','הנופי','העירוני'
    ])[(((i - 1) / 2000) % 10) + 1] AS descriptor_word,
    (ARRAY[
      'דרך הרצל','שדרות בן גוריון','רחוב ויצמן','דרך הים','רחוב הנביאים',
      'שדרות הנשיא','רחוב רוטשילד','דרך העצמאות','רחוב הפלמ"ח','שדרות רבין'
    ])[((i - 1) % 10) + 1] AS street_name
  FROM generate_series(1, 20000) AS g(i)
) q;


-- =====================================
-- ROUTE: 600 rows
-- מובטח start_location שונה מ-end_location
-- =====================================
INSERT INTO ROUTE
(route_id, route_name, start_location, end_location, estimated_duration_minutes, total_distance_km, created_date, region_id)
SELECT
  i,
  route_theme || ' בין ' || start_city || ' ל' || end_city AS route_name,
  start_city,
  end_city,
  40 + (i % 140) AS estimated_duration_minutes,
  ROUND((20 + (i % 160) + (random() * 18))::numeric, 1)::float AS total_distance_km,
  DATE '2025-01-01' + ((i - 1) % 365) AS created_date,
  ((i - 1) % 500) + 1 AS region_id
FROM (
  SELECT
    i,
    (ARRAY[
      'מסלול נוף',
      'מסלול תרבות',
      'מסלול חופים',
      'מסלול מורשת',
      'מסלול טבע',
      'מסלול פנאי',
      'מסלול משפחות',
      'מסלול היסטורי',
      'מסלול קולינרי',
      'מסלול אמנות'
    ])[((i - 1) % 10) + 1] AS route_theme,
    cities[((i - 1) % 10) + 1] AS start_city,
    cities[((i + 2) % 10) + 1] AS end_city
  FROM generate_series(1, 600) AS g(i),
  LATERAL (
    SELECT ARRAY[
      'ירושלים','תל אביב','חיפה','נצרת','עכו',
      'טבריה','צפת','אילת','אשדוד','נתניה'
    ] AS cities
  ) c
) q;
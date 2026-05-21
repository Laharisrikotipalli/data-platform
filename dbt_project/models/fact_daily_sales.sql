-- dbt_project/models/fact_daily_sales.sql
-- Aggregated daily sales fact table joining sales, products, and reviews

{{ config(materialized='table') }}

SELECT
    s.sale_date::DATE                       AS date,
    s.product_id,
    p.name                                  AS product_name,
    p.category                              AS product_category,
    SUM(s.quantity)                         AS total_quantity_sold,
    SUM(s.total_amount)                     AS total_revenue,
    AVG(r.rating)                           AS avg_review_rating
FROM
    raw.sales s
    JOIN raw.products p
        ON s.product_id = p.product_id
    LEFT JOIN raw.reviews r
        ON s.product_id = r.product_id
GROUP BY
    s.sale_date::DATE,
    s.product_id,
    p.name,
    p.category
ORDER BY
    date DESC,
    product_id
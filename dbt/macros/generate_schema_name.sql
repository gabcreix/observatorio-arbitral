{# Un "macro" en dbt es una función reutilizable en Jinja. Este es el override
   estándar de dbt para generate_schema_name: por defecto, dbt concatena el
   schema del target (aquí "silver", el de profiles.yml) con el +schema: de
   cada modelo, dando "silver_staging"/"silver_silver" en vez de "staging"/
   "silver" tal cual. Este override hace que el +schema: de dbt_project.yml
   se respete literal. #}

{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}

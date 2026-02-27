{{ date }}, в [каталог]({{ url }}) PlayStation Plus Extra и выше, будут добавлены:

{% for game in games %}
• {{ game }}
{% endfor %}

В каталог PlayStation Plus Premium добавят:
{% for game in premium_games %}
• {{ game }}
{% endfor %}
#покаинтересно@brknbtns #игры@brknbtns

from datetime import date

from django.db import connection
from django.http import HttpResponse, request, JsonResponse
from django.template.context_processors import csrf
from django.views import generic
from flask import jsonify

from .models import corona_data, country,worldwide_aggregated_data
import plotly
import plotly.graph_objects as go
import chart_studio
import chart_studio.plotly as py
import plotly.express as px
import random
g_layout=go.layout
g_figure=go.Figure
cities = []
from django.shortcuts import get_object_or_404

# Create your views here.
def generate_country_data(request,ajax, centre_countries):
    limits = [(0, 2), (3, 10), (11, 20), (21, 50), (50, 3000)]
    colors = ["rgb(0,116,217)", "rgb(255,65,54)", "rgb(133,20,75)", "rgb(255,133,27)", "red"]

    countries_taken = []
    scale = 50

    country_colors = {}
    maps_data = corona_data.map_data(request)
    for data in maps_data:
        state = ''
        if data.state is None:
            state = ''
        elif data.state=='NULL':
            state=''
        else:
            state = data.state
        country_raw_text = '{0}'.format(data.total_cases) + ' <br> ' + state + '<br> ' + (data.country)
        list_index = '';
        scale= int(data.total_cases / 100)
        if scale > 40:
            scale=40

        list_entry = False
        if data.country in countries_taken:
            list_index = ''
            list_entry = False
        else:
            list_index = '{0}'.format(data.country)
            countries_taken.append(data.country)
            country_colors[data.country] = colors[random.randint(0, 4)]
            list_entry = True

        city = go.Scattergeo(
            locationmode='country names',
            lon=[data.lng],
            lat=[data.lat],
            text=country_raw_text,
            hovertext=country_raw_text,
            marker=go.scattergeo.Marker(
                size=scale,
                opacity=0.5,
                color=country_colors[data.country],
                line=go.scattergeo.marker.Line(
                    width=0.5, color='rgb(40,40,40)'
                ),
                sizemode='area'
            ),
            name=list_index,
            showlegend=list_entry,
        )
        cities.append(city)

    g_layout = go.Layout(
        title=go.layout.Title(
            text='Corona Effect'
        ),
        showlegend=True,
        geo=go.layout.Geo(
            scope='world',
            projection=go.layout.geo.Projection(
                type='natural earth'
            ),
            showland=True,
            landcolor='rgb(217, 217, 217)',
            subunitwidth=1,
            countrywidth=1,
            showcountries=True,
            subunitcolor="rgb(255, 255, 255)",
            countrycolor="rgb(255, 255, 255)"
        ),
        height=600,
        width=600,
        paper_bgcolor="#222a42",
        plot_bgcolor="#222a42",
        legend_orientation="h",
        margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )
    if ajax == 1:
        g_layout.geo.center = dict(centre_countries)
        g_layout.geo.projection.rotation=dict(centre_countries)
        g_layout.geo.projection.scale = 4

    g_figure = go.Figure(data=cities, layout=g_layout)
    g_figure.update_layout(legend={'itemsizing': 'constant','y':-0.005,
                              'font':{'color':'white'}})

    return plotly.offline.plot(g_figure, filename='bubble_map', auto_open=False, output_type='div')

def get_line_chart(country_param):
    cursor = connection.cursor()

    query = 'SELECT DATE_FORMAT(s3.day_date, "%M, %y"),s3.total_confirmed , s3.total_death, s3.total_recovered FROM ( SELECT s1.updated_at as day_date, SUM(s1.confirmed) as total_confirmed, SUM(s1.deaths) as total_death, SUM(s1.recovered) as total_recovered  FROM corona_corona_data AS s1 JOIN corona_corona_data AS s2 ON s1.country = s2.country AND s1.state = s2.state AND s1.updated_at > s2.updated_at GROUP BY s1.updated_at ) s3 GROUP BY DATE_FORMAT(s3.day_date, "%Y-%m") HAVING MAX(s3.day_date)';
    cursor.execute(query)

    month_data = cursor.fetchall()
    x_arr = []
    y_arr = []
    death_y_arr=[]
    recovered_y_arr=[]
    for ri in month_data:
        x_arr.append(ri[0])
        y_arr.append(ri[1])
        death_y_arr.append(ri[2])
        recovered_y_arr.append(ri[3])

    confirmed_trace=go.Scatter(
        x=x_arr,
        y=y_arr,
        marker=dict(
            color='gold'
        ),
        name='Confirmed'
    )
    death_trace = go.Scatter(
        x=x_arr,
        y=death_y_arr,
        marker=dict(
            color='red'
        ),
        name='Death'
    )
    recovered_trace = go.Scatter(
        x=x_arr,
        y=recovered_y_arr,
        marker=dict(
            color='green'
        ),
        name='Recovered'
    )

    fig = go.Figure(data=[confirmed_trace,death_trace,recovered_trace])
    fig.update_xaxes(tickfont=dict(color='white', size=14))
    fig.update_yaxes(tickfont=dict(color='white', size=14))
    fig.update_layout(paper_bgcolor="#222a42",
                      plot_bgcolor="#222a42",
                      legend={'font': {'color': 'white'}}
                      )
    return plotly.offline.plot(fig, filename='line_map', auto_open=False, output_type='div')


def change_country_data(request):
    centre_countries = dict()
    country_param = ''
    if request.GET.get('country',None):
        country_param = request.GET.get('country',None)
        country_data=country.objects.filter(country=country_param)[0]
        centre_countries['lon'] = country_data.lng
        centre_countries['lat'] = country_data.lat
    else:
        country_param = '';

    #######################   Load Main Map ################################

    output_data_total_confirmed = corona_data.total_countries_confirmed(request, country_param)
    output_data_total_deaths = corona_data.total_countries_deaths(request, country_param)
    output_data_total_recovered = corona_data.total_countries_recovery(request, country_param)

    ############## Generate Line Chart Country Wise #########################
    return JsonResponse({'data':generate_country_data(request,1,centre_countries),
                         'total_confirmed':output_data_total_confirmed['total_cases'],
                         'total_deaths': output_data_total_deaths['total_cases'],
                         'total_recovered': output_data_total_recovered['total_cases']
                         }, status = 200)


class IndexView(generic.ListView):
    template_name = 'corona/index.html'
    context_object_name = 'country_wise_cases'

    def get_queryset(self):
        return generate_country_data(self,0,'')
            #return py.plot(fig, filename='bubble_map',auto_open=False,sharing='public')

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Corona Details'

        ###################### Total cases in Table Format #######################
        context['maps_data'] =corona_data.all_countries_confirmed(self,'')

        ################## Line Chart DAta #####################

        context['month_wise_data'] =  get_line_chart('')

        ######### Total deaths #################

        context['total_confirmed'] = corona_data.total_countries_confirmed(self,'')
        context['total_deaths'] = corona_data.total_countries_deaths(self, '')
        context['total_recovered'] = corona_data.total_countries_recovery(self, '')

        ############## Time Series DAta #####################
        time_series_data=worldwide_aggregated_data.objects.only('Date','IncreaseRate','Confirmed','Deaths','Recovered')
        month_arr = []
        confirmed_cases_arr = []
        deaths_cases_arr = []
        recovered_cases_arr = []
        marker_size=[]
        for ri in time_series_data:
            month_arr.append(ri.Date)
            confirmed_cases_arr.append(ri.Confirmed)
            deaths_cases_arr.append(ri.Deaths)
            recovered_cases_arr.append(ri.Recovered)
            marker_size.append(15)

        confirmed_trace=go.Scatter(
            x=month_arr,
            y=confirmed_cases_arr,
            mode='markers',
            marker_size=marker_size,
            marker=dict(
                color='gold'
            ),
            name='Confirmed'
        )
        death_trace = go.Scatter(
            x=month_arr,
            y=deaths_cases_arr,
            mode='markers',
            marker_size=marker_size,
            marker=dict(
                color='crimson'
            ),
            name='Death'
        )
        recovered_trace = go.Scatter(
            x=month_arr,
            y=recovered_cases_arr,
            mode='markers',
            marker_size=marker_size,
            marker=dict(
                color='green'
            ),
            name='Recovered'
        )

        fig_time_Series = go.Figure(data=[confirmed_trace,death_trace,recovered_trace])
        fig_time_Series.update_xaxes(tickfont=dict(color='white', size=14))
        fig_time_Series.update_yaxes(tickfont=dict(color='white', size=14))
        fig_time_Series.update_layout(paper_bgcolor="#222a42",
                          plot_bgcolor="#222a42",legend={'font': {'color': 'white'}})
        context['time_series_data'] = plotly.offline.plot(fig_time_Series, filename='time_Series_map', auto_open=False, output_type='div')

        return context

import warnings
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from re import sub
from decimal import Decimal
from scipy import stats
import seaborn as sns
from textwrap import fill
from wordcloud import WordCloud
import folium as fl
from folium.plugins import HeatMap
from folium.plugins import PolyLineTextPath
from urllib.request import Request, urlopen


warnings.filterwarnings('ignore')
pd.set_option('display.max_columns', 100)
pd.set_option('display.max_rows', 100)

# this script assumes the use of a airbnb listings file in csv format "
# set variables and functions #
#location of listings csv data:

listings_file = 'data/listings 2.csv'

'''set variable for with type of room you are interested in:
    'Entire home/apt'
    'Private room'
    'Hotel room'
    'Shared room'
    To return all room types, set value to 'All'
'''
room_type = 'All'

#list of columns you want to keep:
keeper_columns = ['id',
                'name',
                'host_id',
                'host_name',
                'neighbourhood',
                'neighborhood_overview',
                'host_since',
                'host_location',
                'host_listings_count',
                'host_total_listings_count',
                'neighbourhood',
                'latitude',
                'longitude',
                'room_type',
                'price',
                'minimum_nights',
                'number_of_reviews',
                'last_review',
                'reviews_per_month',
                'calculated_host_listings_count',
                'availability_30',
                'availability_365',
                'number_of_reviews_ltm',
                 'number_of_reviews_l30d',
                 'first_review',
                 'last_review',
                 'review_scores_rating',
                 'review_scores_accuracy',
                 'review_scores_cleanliness',
                 'review_scores_location', 'review_scores_value',
                 'license',
                 'calculated_host_listings_count',
                  'calculated_host_listings_count_entire_homes',
                  'calculated_host_listings_count_private_rooms',
                  'calculated_host_listings_count_shared_rooms',
                 'reviews_per_month',
                  'gross_income_30',
                  'airbnb_host_fee',
                  'airbnb_profit_30',
                  'bedrooms',
                  'bathrooms',
                  'bathrooms_text',
                  'cleaning_fee',
                  'percentage_occupied',
                  'net_income_30',
                  'cleaners_fee_30'
                 ]

#function to filter to specific room types (set to True by default), drop columns not in keeper_columns variable, modify price data type to int vs string, provide information summary statement


def read_in_data(file_path_for_file):
    return pd.read_csv(file_path_for_file)


def pie_chart_for_column_value_by_percentage(df, column, title, imagename):
    labels = df[column].value_counts().index
    sizes = df[column].value_counts().values
    #explode = (0.1, 0, 0, 0)
    fig1, ax1 = plt.subplots(figsize=(10,10))
    ax1.pie(sizes,  autopct='%1.1f%%',labels=sizes,
        shadow=False, startangle=90, pctdistance=.5, labeldistance=1.05)
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    ax1.legend(bbox_to_anchor=(1.0, 1.0), labels=labels, loc='upper right')
    plt.title(title)
    plt.savefig('images/' + imagename + '.png')
    plt.tight_layout()
    plt.show()


# establish formula for cleaning fee per listing
def determine_avg_cleaning_fee(df):
    conditions = [
        (df['bedrooms'] == 0) & (df['bathrooms_text'].str.contains('0')==True),
        (df['bedrooms'] == 0) & (df['bathrooms_text'].str.contains('1|1.') ==True),
        (df['bedrooms'] == 1.0) & (df['bathrooms_text'].str.contains('1|1.') ==True),
        (df['bedrooms'] == 2.0) &  (df['bathrooms_text'].str.contains('1|1.|2|2.') ==True),
        (df['bedrooms'] == 3.0) & (df['bathrooms_text'].str.contains('1|1.|2|2.') ==True),
        (df['bedrooms'] == 4.0) & (df['bathrooms_text'].str.contains('1|1.|2|2.') ==True),
        (df['bedrooms'] == 4.0) & (df['bathrooms_text'].str.contains('2|2.|3|3.') ==True),
        (df['bedrooms'] == 5.0) & (df['bathrooms_text'].str.contains('2|2.|3|3.') ==True),
        (df['bedrooms'] > 5.0) & (df['bathrooms_text'].str.contains('4|4.|5|5.|6|6.') ==True)
    ]
    choices = [0,25,50,95,125,150,175,200,350]
    df['cleaning_fee'] = np.select(conditions, choices, default=0)
    return df

    #create new columns for pricing, fees, and profit
    #drop columns you don't want to keep
    #keep only those listings which are for the Entire Home for less than 30 days as those are illegal in Asheville


def keep_pertinent_listings_data(df, by_room_type=True, room_type='Entire home/apt'):
    if by_room_type:
        df= df[df['room_type'] == room_type]
    df['price'] = df['price'].str.replace("[$, ]", "").astype("float")
    df['price'] = df['price'].astype("int")
    df['minimum_nights'] = df['minimum_nights'].astype("int")
    df['neighbourhood'] = df['neighbourhood'].str.split(',').str[0]
    days_booked= 30 - df['availability_30']
    df['cleaners_fee_30'] = df['cleaning_fee'] * (days_booked / df['minimum_nights'])
    df['gross_income_30'] = (df['price'] * days_booked) + df['cleaners_fee_30']
    df['airbnb_host_fee'] = 0.03 * df['gross_income_30']
    df['airbnb_profit_30'] = df['airbnb_host_fee'] + (0.14 * df['gross_income_30'])
    df['percentage_occupied'] = ((30 - df['availability_30']) / 30 * 100).astype('int')
    df['net_income_30'] = df['gross_income_30']- df['airbnb_host_fee'] - df['cleaners_fee_30']
    new_df = df.drop(columns=[col for col in df if col not in keeper_columns])
    new_df= new_df.query('minimum_nights < 30')
    print(f"There are {new_df['id'].count()} entries for {room_type} listings, there are {new_df['license'].count()} licenses.")
    return new_df

def determine_entire_home_rentals_less_than_30_days_pie_chart(original_df, cleaned_df, title='Percentage of Stays Violating Ordnance'):
    entire_home_stays_less_than_30 = len(cleaned_df)
    entire_home_stays_30days_orlonger = len(original_df.loc[original_df['room_type']=='Entire home/apt']) - entire_home_stays_less_than_30
    all_other_listings_count= len(original_df)- (entire_home_stays_less_than_30 + entire_home_stays_30days_orlonger)
    labels_count=[all_other_listings_count, entire_home_stays_less_than_30, entire_home_stays_30days_orlonger]
    labels_list=['Other Stays', 'Entire Home Stays For Less Than Thirty', 'Entire Home Stays Over Thirty']
    sizes=[all_other_listings_count, entire_home_stays_less_than_30, entire_home_stays_30days_orlonger]
    fig1, ax1 = plt.subplots(figsize=(10,10))
    ax1.pie(sizes,  autopct='%1.1f%%',labels=labels_count, pctdistance=.5, labeldistance=1.05,
        shadow=False, startangle=90)
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    ax1.legend(bbox_to_anchor=(1.0,1.0), labels=labels_list, loc='upper right')
    plt.title(title)
    plt.savefig('images/' + title + ' piechart.png')
    plt.tight_layout()
    plt.show()



def calculate_distributions(df,df_column):
    df_column=df[df_column]
    df_column_median = int(round(np.median(df_column),2))
    df_column_mean = int(round(np.mean(df_column),2))
    mode_1 = list(stats.mode(df_column))
    df_column_mode = mode_1[0]
    df_column_min_value=df_column.min()
    df_column_max_value=df_column.max()
    quantiles= df_column.quantile([0.25,0.5,0.75])

    return df_column_median,df_column_mean,df_column_mode,df_column_min_value,df_column_max_value,quantiles



def determine_and_update_poss_mistaken_price(df):
    min_logical_price = price_first_quantile * 25
    max_prices = df.query('(price > @min_logical_price) and (minimum_nights >= 30)')
    if len(max_prices) > 0:
        max_index = max_prices['price'].index.values
        print(f'Nightly price may be input error, look closer at index {max_index} with nightly price of {max_prices.values}')
        modify_price=input("Modify the price to average nightly price? yes/no :")
        if modify_price == 'yes':
            df.loc[df.price > min_logical_price, 'price'] = price_mode

    return df


def get_qualitative_dist_box_plot(df, df_column, ylabel, title, imagename, color='magenta'):
    df_column=df[df_column]
    median = round(np.median(df_column),2)
    mean = round(np.mean(df_column),2)
    mode_1 = list(stats.mode(df_column))
    fin_mode = list(mode_1)[0]
    min_int=df_column.min()
    max_int=df_column.max()
    #print([min_int, max_int, median,mean,mode])
    fig, ax = plt.subplots(figsize =(10, 8))
    sns.boxplot(y= df_column,
            color=color,
            showmeans=True,
            hue = df_column,
            meanprops={"marker":"o",
                       "markerfacecolor":"yellow",
                       "markeredgecolor":"black",
                      "markersize":"14"},
            medianprops=dict(color='red'),
            width = 0.5
               )
    plt.title(title, fontsize=14)
    plt.ylabel(ylabel)
    plt.legend(labels=[f"Min Value = {min_int} ",f"Max Value = {max_int}", f"Mean Value = {mean}", f"Median Value = {median}", f"Mode Value = {fin_mode}"], title = 'Qualitative Distributions')
    plt.savefig(f'images/{imagename}' + '.png')
    plt.show()


#function to build distribution histogram for user defined column-data
def build_distribution_histogram(column_data,color, figsize_list, bins_int, step_size, ylabel, xlabel,title,imagename):
  #ensure user-provided variables are correct data-type:
    min_int=column_data.min()
    max_int=column_data.max()
    bins_int=int(bins_int)
    step_size=int(step_size)
    ylabel=str(ylabel)
    xlabel=str(xlabel)
    title=str(title)
    imagename=str(imagename)

  #build histogram plot:
    plt.figure(figsize=(figsize_list[0],figsize_list[1]))
    plt.hist(column_data, bins=bins_int, color=str(color))
    plt.xticks(np.arange(min_int, max_int, step=step_size))
    plt.ylabel(ylabel)
    plt.xlabel(xlabel)
    #plt.axvline(x.mean(), color='k', linestyle='dashed', linewidth=1, label=)
    plt.title(title)
    plt.legend([f'Min Value:{min_int}',f'Max Value:{max_int}'], loc='upper right')
    plt.savefig(f'images/{imagename}' +'.png')
    plt.show()


def make_bar_chart_from_column_values_with_values_top20(df,df_column,figsize=(30,5), title='Title', color='Orange', imagename='imagename'):
    df_column = df[df_column]
    top_values= df_column.value_counts()[:20]
    high_value= top_values.values[0]
    low_value=top_values.values[-1]
    fig,ax = plt.subplots(figsize=figsize)
    plt.bar(range(len(top_values)), top_values.values, align='center', color= color)
    for i in range(len(top_values.values)):
            plt.annotate(str(top_values.values[i]), xy=(i,top_values.values[i]), ha='center', va='bottom')
    plt.xticks(range(len(top_values)), top_values.index.values, size='medium', rotation=45)
    plt.legend(labels=[f"Highest Value = {high_value}", f"Lowest Value = {low_value}"])
    plt.title(title)
    plt.xlabel(title)
    plt.savefig(f"images/{imagename}" + ".png")
    plt.show()


def make_bar_chart_from_column_values_with_names_top20(df,df_column, df_column_for_name_label, figsize=(30,5), title='Title', color='Orange', imagename='bar_chart_names'):
    df_column = df[df_column]
    top_values= df_column.value_counts()[:20]
    list_of_value_names=[]
    for each in top_values.index.values:
       list_of_value_names.append(df.query('@df_column == @each')[df_column_for_name_label].values[0])
    high_value= top_values.values[0]
    low_value=top_values.values[-1]
    fig,ax = plt.subplots(figsize=figsize)
    plt.bar(range(len(top_values)), top_values.values, align='center', color= color)
    for i in range(len(top_values.values)):
            plt.annotate(str(top_values.values[i]), xy=(i,top_values.values[i]), ha='center', va='bottom')
    plt.xticks(range(len(top_values)), list_of_value_names, size='medium', rotation=45)
    plt.legend(labels=[f"Highest Value = {high_value}", f"Lowest Value = {low_value}"])
    plt.savefig(f"images/{imagename}" + ".png")
    plt.title(title)
    plt.show()

def draw_map(df):
    asheville_center = [df.latitude.mean(), df.longitude.mean()]
    zones = df.groupby('neighbourhood').mean().reset_index()
    zone_name = zones['neighbourhood'].values.tolist()
    zone_loc = zones[['latitude', 'longitude']].values.tolist()

    base_map = fl.Map(location = asheville_center, control_scale = True, zoom_start = 12, tiles = 'OpenStreetMap')

    for i in range(len(zone_name)):
        attr = {'fill': 'midnightblue', 'font-weight': 'bold', 'font-size': '20'}
        pl = fl.PolyLine([[zone_loc[i][0], zone_loc[i][1]-.1], [zone_loc[i][0], zone_loc[i][1]+.1]], weight = 15, color = 'rgb(255,255,255, 0)')
        base_map.add_child(pl)
        base_map.add_child(PolyLineTextPath(pl, text = zone_name[i], attributes = attr, center = True))

    return base_map


def determine_theoretical_profit(df,median_value):
    return median_value * len(df)


######################################################


## if name equals main block #####


if __name__ == "__main__":

    listings_detailed_df = read_in_data(listings_file)

    pie_chart_for_column_value_by_percentage(listings_detailed_df,'room_type','Asheville AirBnB Listings By Room Type', 'All Room Type by Percentage')

    new_listings_with_cleaning_df = determine_avg_cleaning_fee(listings_detailed_df)
    new_listings_df = keep_pertinent_listings_data(new_listings_with_cleaning_df)

    price_median = calculate_distributions(new_listings_df,'price')[0]
    price_mean = calculate_distributions(new_listings_df,'price')[1]
    price_mode = calculate_distributions(new_listings_df,'price')[2]
    price_min = calculate_distributions(new_listings_df,'price')[3]
    price_max =calculate_distributions(new_listings_df,'price')[3]
    price_first_quantile= int(calculate_distributions(new_listings_df,'price')[5][0.25])
    min_logical_price = price_first_quantile * 25
    max_prices = new_listings_df.query('(price > @min_logical_price) and (minimum_nights >=30)')['price']

    price_corrected_df = determine_and_update_poss_mistaken_price(new_listings_df)
    determine_entire_home_rentals_less_than_30_days_pie_chart(listings_detailed_df, price_corrected_df, title='Percentage of Stays Violating Ordnance')

    # set the column in data which will be used for price:
    prices = price_corrected_df['price']

    #draw map showing distribution of listings
    base_map = draw_map(price_corrected_df)
    base_map.add_child(HeatMap(data = price_corrected_df[['latitude', 'longitude']], min_opacity = 0.4, radius = 15, blur = 40))
    base_map.add_child(fl.ClickForMarker(popup='High amount of listings'))
    outfp='images/Asheville.html'
    base_map.save(outfp)

    plt.figure(figsize=(10,10))
    ax = sns.countplot(price_corrected_df['neighbourhood'],hue=price_corrected_df['room_type'])

    get_qualitative_dist_box_plot(price_corrected_df,'price', 'Price', 'Distribution of Nightly Prices', 'Price Distribution boxplot', color='cyan')

    build_distribution_histogram(prices,'green',[20,5],150,100,'Number of listings at price','Price','Distribution of Prices','prices_function_graph')

    price_values=prices.value_counts()[:20]
    plt.figure(figsize=(30,5))
    plt.bar(range(len(price_values)), price_values.values, align='center',)
    plt.xticks(range(len(price_values)), price_values.index.values, size='small')
    plt.title('Top 20 Most Occuring Nightly Prices')
    plt.ylabel('Count of Prices')
    plt.xlabel('Nightly Price')
    plt.savefig('images/Top 20 Most Occuring Nightly Prices.png')
    plt.show()


    price_corrected_df.groupby(by='host_id')['calculated_host_listings_count_entire_homes'].count().value_counts().plot(xlabel='Listings Per Host',  ylabel= 'Number of Hosts', kind='bar', figsize=(15,10), title= 'Total Entire Home Listings Per Host', color='purple',fontsize=14)

    indexes= price_corrected_df.groupby(by='host_id')['calculated_host_listings_count_entire_homes'].count().value_counts().values
    for i in range(0,len(indexes)):
        plt.annotate(str(indexes[i]), xy=(i,indexes[i]),ha='center', va='bottom')
    plt.savefig('images/Total Entire Home Listings per Host.png')


    make_bar_chart_from_column_values_with_names_top20(price_corrected_df,'host_id', 'host_name', figsize=(30,5), title='Asheville Hosts With the Most Listings in Asheville', color='Orange', imagename='Hosts With the Mosts_names')


    get_qualitative_dist_box_plot(price_corrected_df, 'net_income_30', 'Monthly Listing Net Income OCT 2021','Real Host Monthly Net Income/Listing OCT 2021','Real Host Monthly Net Income OCT 2021', color=(0.1, 0.4, 0.3))

    get_qualitative_dist_box_plot(price_corrected_df, 'airbnb_profit_30', 'AirBnB Monthly Profit/Listing OCT 2021','AirBnB Monthly Profit/Listing OCT 2021','AirBnB Monthly Profit OCT 2021', color='magenta')

    get_qualitative_dist_box_plot(price_corrected_df, 'cleaners_fee_30', 'Cleaners Monthly Profit/Listing OCT 2021','Cleaners Monthly Profit/Listing OCT 2021','Cleaners Monthly Profit OCT 2021', color='yellow')


    calculate_distributions(price_corrected_df,'airbnb_profit_30')[0] * len(price_corrected_df)


    total_airbnb_profit = determine_theoretical_profit(price_corrected_df,calculate_distributions(price_corrected_df,'airbnb_profit_30')[0])
    total_host_profit = determine_theoretical_profit(price_corrected_df,calculate_distributions(price_corrected_df,'net_income_30')[0])
    total_cleaners_profit = determine_theoretical_profit(price_corrected_df,calculate_distributions(price_corrected_df,'cleaners_fee_30')[0])

    names = ['Airbnb Profit', 'Host Profit', 'Cleaners Profit']
    values = [int(total_airbnb_profit), int(total_host_profit), int(total_cleaners_profit)]
    fig,ax = plt.subplots(figsize=(10,10))
    plt.bar(names, values)
    plt.ticklabel_format(useOffset=False, style='plain', axis='y')
    plt.ylabel('Monthly Profits in USD')
    plt.suptitle('All Monthly Profits ')
    plt.savefig('images/All Monthly Profits.png')
    plt.show()

    print('completed')





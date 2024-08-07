import os
import csv
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats
import seaborn as sns
import statsmodels.api as sm


def get_player_info(club_urls):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/58.0.3029.110 Safari/537.3'}  # Setting user agent for accessing the data

    response = requests.get(club_urls,
                            headers=headers)  # Sending GET request

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')  # Parsing HTML content via BeautifulSoup

        player_rows = soup.select('table.items > tbody > tr')
        players_info = []  # Extracting information about the HTML

        for row in player_rows:
            columns = row.find_all(['th', 'td'])
            name = columns[3].get_text(strip=True)
            value = columns[7].get_text(strip=True)

            players_info.append({'name': name, 'value (mln euros)': value})  # Appending columns

        return players_info
    else:
        print(f"Failed to fetch data from {club_urls}")  # Get information about failure
        return None


def clean_value(value):
    if 'm' in value:
        return float(value.replace('€', '').replace('m', '').replace('bn', ''))

    if 'k' in value:
        return float(value.replace('€', '').replace('k', '')) / 1000  # Cleaning values and converting them to millions

    return None


def save_to_csv(clubs_name, players_info):  # Saving players' information to .csv files
    csv_folder = "csv_files"  # Additionally creating a folder for .csv files
    if not os.path.exists(csv_folder):
        os.makedirs(csv_folder)
        print(f"Folder for CSV files ({csv_folder}) has been created.")

    csv_file_path = os.path.join(csv_folder, f"{clubs_name}_values.csv")

    with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['name', 'club_name', 'value (mln euros)'])
        writer.writeheader()

        for player in players_info:
            player['club_name'] = clubs_name.replace("-", " ")
            writer.writerow({'name': player['name'], 'club_name': player['club_name'],
                             'value (mln euros)': clean_value(player['value (mln euros)'])})  # Saving data cleaned


def merge_csv_files():
    csv_folder = "csv_files"
    all_files = [file for file in os.listdir(csv_folder) if file.endswith("_values.csv")]  # Find files *_values.csv

    if not all_files:
        print("Error: CSV files not found for merging.")  # Print a message if no .csv files are given
        return

    df_list = []
    for file in all_files:
        df = pd.read_csv(os.path.join(csv_folder, file))
        df_list.append(df)  # Appending files

    merged_df = pd.concat(df_list, ignore_index=True)
    merged_df.to_csv(os.path.join(csv_folder, "merged_values.csv"), index=False)
    print("Files merged successfully")  # Print a message if merging was successful


def create_images_folder():
    if not os.path.exists("images"):
        os.makedirs("images")
        print("Folder for images has been created")  # Create a folder for storing the images


def plot_distribution(data, team_name):
    plt.figure(figsize=(8, 5))
    sns.histplot(data['value (mln euros)'], kde=True, color='r', stat='density')  # Plot histogram + KDE

    mean, std = data['value (mln euros)'].mean(), data['value (mln euros)'].std()
    xmin, xmax = plt.xlim()
    x = np.linspace(xmin, xmax, 100)
    p = stats.norm.pdf(x, mean, std)
    plt.plot(x, p, 'c', linewidth=2)  # Normal distribution curve

    plt.title(f'Distribution of Transfer Values for {team_name}')
    plt.xlabel('Transfer Value (mln euros)')
    plt.ylabel('Density')

    img_path = os.path.join("images", f"{team_name}_normal_distribution.png")  # Saving the plot as .png
    plt.savefig(img_path)
    plt.show()

    return img_path


def plot_scatter(data, team_name):
    plt.figure(figsize=(8, 5))
    sns.scatterplot(data=data, x='name', y='value (mln euros)', hue='club_name', palette='colorblind', s=100)
# Plot scatter plot
    plt.title(f'Scatter Plot of Transfer Values for {team_name}')
    plt.xlabel('Player Name')
    plt.ylabel('Transfer Value (mln euros)')
    plt.xticks(rotation=40, ha='right', fontsize=5)

    img_path = os.path.join("images", f"{team_name}_scatter.png")  # Saving the plot as .png
    plt.savefig(img_path)
    plt.show()

    return img_path


def plot_combined_scatter(data):
    plt.figure(figsize=(11, 7))
    sns.scatterplot(data=data, x='name', y='value (mln euros)', hue='club_name', palette='colorblind', s=100)

    plt.title('Combined Scatter Plot of Transfer Values')
    plt.xlabel('Player Name')
    plt.ylabel('Transfer Value (mln euros)')
    plt.xticks(rotation=40, ha='right', fontsize=5)

    img_path = os.path.join("images", "combined_scatter.png")
    plt.savefig(img_path)
    plt.show()

    return img_path


def plot_combined_scatter_regression(data):
    data = data.dropna(subset=['value (mln euros)'])  # Drop NaNs if there are any
    x = data['value (mln euros)']
    y = data.index

    X = sm.add_constant(x)  # Constant to the independent variable

    model = sm.OLS(y, X)  # Creating Simple OLS
    results = model.fit()

    y_pred = results.predict(X)  # Predict the values

    plt.scatter(x, y, label="", color='r')  # Plot scatter plot with OLS regression line

    plt.plot(x, y_pred, color='k', linewidth=2, label=f'OLS Regression for all teams')  # Details for plot

    plt.xlabel('Transfer Value (mln euros)')
    plt.ylabel('Player Index')
    plt.legend()
    plt.title(f'Scatterplot with OLS Regression for all of the teams')
    plt.show()

    img_path = os.path.join("images", "regression.png")
    plt.savefig(img_path)

    return img_path


def generate_files_list(clubs):  # Generate list of files names
    files = []
    for club_url in clubs:
        club_name = club_url.split('/')[-4]
        files.append(f"{club_name}_normal_distribution.png")
        files.append(f"{club_name}_scatter.png")
        files.append(f"{club_name}_values.csv")

    files.append("combined_scatter.png")
    files.append("regression.png")
    files.append("merged_values.csv")

    return files


def save_files_list(files):  # Saving as .txt
    with open("files_list.txt", "w") as file:
        for f in files:
            file.write(f"{f}\n")


def main():
    create_images_folder()  # Creating the folder for images
    num_clubs = int(input("Enter the number of clubs you want to input: "))  # Asking for input
    clubs = []

    for _ in range(num_clubs):
        club_url = input(
            "Enter the Transfermarkt link for a club (example: "
            "https://www.transfermarkt.com/fc-arsenal/startseite/verein/11): ")
        clubs.append(club_url)  # Input URLs for each club

    for club_url in clubs:
        club_name = club_url.split('/')[-4]
        player_info = get_player_info(club_url)  # Process the data

        if player_info:
            save_to_csv(club_name, player_info)
            print(f"CSV file for {club_name} created successfully.")
            df = pd.read_csv(os.path.join("csv_files", f"{club_name}_values.csv"))  # Read the .csv file

            plot_distribution(df, club_name)
            plot_scatter(df, club_name)  # Generate plots

    merge_csv_files()  # Merge files

    merged = pd.read_csv(os.path.join("csv_files", "merged_values.csv"))  # Add file to folder

    plot_combined_scatter(merged)
    plot_combined_scatter_regression(merged)
    files = generate_files_list(clubs)
    save_files_list(files)


if __name__ == "__main__":
    main()

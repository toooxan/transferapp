import os
from flask import Flask, render_template, request, send_file, send_from_directory, redirect, url_for
from test import get_player_info, save_to_csv, merge_csv_files, plot_distribution, plot_scatter, plot_combined_scatter, \
    plot_combined_scatter_regression
import pandas as pd
import shutil
import zipfile

app = Flask(__name__)


def create_folders():  # Function to create necessary folders for storing CSV files and images
    folders = ['images', 'csv_files']
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"Created '{folder}' folder.")


def create_zip_file():  # Function to create a zip file containing specified folders
    folders_to_zip = ['images', 'csv_files']
    return zip_folders(folders_to_zip)


@app.route('/')  # Flask route for the home page
def index():
    return render_template('index.html')


@app.route('/run_analysis', methods=['POST'])  # Flask route for analyzing data submitted via the web form
def analyze():
    create_folders()  # Creating necessary folders if they don't exist

    num_clubs = int(request.form['num_clubs'])  # Extract number of clubs and their URLs from the submitted form
    clubs = []

    for i in range(1, num_clubs + 1):
        club_url = request.form.get(f'club_url_{i}')
        if club_url:
            clubs.append(club_url)

    for club_url in clubs:
        club_name = club_url.split('/')[-4]
        player_info = get_player_info(club_url)

        if player_info:
            save_to_csv(club_name, player_info)  # Save player information to CSV file and generate plots
            print(f"CSV file for {club_name} created successfully.")
            df = pd.read_csv(os.path.join('csv_files', f"{club_name}_values.csv"))

            plot_distribution(df, club_name)
            plot_scatter(df, club_name)

    merge_csv_files()

    merged = pd.read_csv(os.path.join('csv_files', "merged_values.csv"))

    plot_combined_scatter(merged)
    plot_combined_scatter_regression(merged)

    upload_folders(['images', 'csv_files'])  # Move uploaded folders to the static/uploads directory
    delete_folders(['images', 'csv_files'])  # Delete original folders to clean up

    zip_path = create_zip_file()  # Create a zip file containing the analysis results

    return redirect(url_for('result', zip_path=zip_path))  # Redirect to the result page after the analysis is completed


@app.route('/result')  # Flask route for displaying the result page
def result():
    zip_path = request.args.get('zip_path')
    return render_template('result.html', zip_path=zip_path)


@app.route('/download_result/<zip_path>')  # Flask route for downloading the zip file containing analysis results
def download_result(zip_path):
    return send_file(zip_path, as_attachment=True)


def upload_folders(folders):  # Function to move folders to the static/uploads directory
    for folder in folders:
        shutil.move(folder, os.path.join('static', 'uploads', folder))


def zip_folders(folders):  # Function to zip specified folders
    zip_filename = 'generated_folders.zip'
    zip_path = os.path.join('static', 'uploads', zip_filename)

    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for folder in folders:
            folder_path = os.path.join('static', 'uploads', folder)
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, folder_path)
                    zipf.write(file_path, arcname)

    return zip_path


def delete_folders(folders):  # Function to delete folders in the static/uploads directory
    for folder in folders:
        folder_path = os.path.join('static', 'uploads', folder)
        shutil.rmtree(folder_path, ignore_errors=True)
        print(f"Deleted folder: {folder_path}")


if __name__ == '__main__':
    app.run(debug=True)

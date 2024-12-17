from flask import Flask, render_template, request, redirect, url_for, send_file, Response
import os
from fpdf import FPDF
from scraping_logic import get_search_results, append_to_pdf, create_folder, create_pdf_file, check_article_existence

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        topic = request.form['topic']
        num_results = int(request.form['num_results'])
        return redirect(url_for('scrape', topic=topic, num_results=num_results))
    return render_template('index.html')


@app.route('/scrape', methods=['GET'])
def scrape():
    topic = request.args.get('topic')
    num_results = int(request.args.get('num_results'))

    def generate():
        results = []
        yield f'data: Scraping started...\n\n'
        yield f'data: 0/{num_results} URLs scraped\n\n'
        yield f'data: progress:0\n\n'  # Initialize the progress bar at 0%

        search_results = get_search_results(topic, num_results)

        for i, url in enumerate(search_results, start=1):
            if check_article_existence(url):
                results.append(url)
                yield f'data: {i}/{num_results} URLs scraped\n\n'
                progress_percentage = int((i / num_results) * 100)
                # Update the progress bar
                yield f'data: progress:{progress_percentage}\n\n'

        yield f'data: Scraping finished. Generating PDF...\n\n'
        yield f'data: progress:100\n\n'  # Set progress bar to 100% when done

        # Create a PDF
        file_directory = create_folder()
        pdf_file_path = create_pdf_file(topic, file_directory)

        pdf = FPDF()
        pdf.add_page()

        # Append content to the PDF
        paras = set()
        append_to_pdf(paras, pdf, results)
        pdf.output(pdf_file_path)

        yield f'data: PDF generated. Redirecting for download...\n\n'
        yield f'data: done {pdf_file_path}\n\n'

    return Response(generate(), mimetype='text/event-stream')


@app.route('/download', methods=['GET'])
def download():
    file_path = request.args.get('file_path', None)
    if file_path:
        # Serve the file with the appropriate headers to prompt a download
        return send_file(file_path, as_attachment=True, download_name=os.path.basename(file_path))
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)

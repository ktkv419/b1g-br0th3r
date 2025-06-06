from yattag import Doc
import os, datetime

REPORT_DIR = os.getenv("REPORT_DIR")

if not (os.path.isdir(REPORT_DIR)):
    os.makedirs(REPORT_DIR)

def generate_similarity_report(similarity_data):
    doc, tag, text = Doc().tagtext()
    
    doc.asis('<!DOCTYPE html>')
    with tag('html'):
        with tag('head'):
            with tag('title'):
                text('Student Work Similarity Report')
            
            # Add CSS styling
            with tag('style'):
                doc.asis("""
                    body {
                        font-family: Arial, sans-serif;
                        margin: 40px;
                        background-color: #f5f5f5;
                        line-height: 1.6;
                    }
                    .header {
                        background-color: #2c3e50;
                        color: white;
                        padding: 20px;
                        text-align: center;
                        border-radius: 8px;
                        margin-bottom: 20px;
                    }
                    .summary {
                        background-color: white;
                        padding: 20px;
                        margin: 20px 0;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }
                    .table-container {
                        background-color: white;
                        border-radius: 8px;
                        overflow: hidden;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }
                    table {
                        width: 100%;
                        border-collapse: collapse;
                    }
                    th, td {
                        padding: 12px;
                        text-align: left;
                        border-bottom: 1px solid #ddd;
                    }
                    th {
                        background-color: #34495e;
                        color: white;
                        font-weight: bold;
                    }
                    tr:hover {
                        background-color: #f8f9fa;
                    }
                    .similarity-high {
                        background-color: #e74c3c;
                        color: white;
                        padding: 4px 8px;
                        border-radius: 4px;
                        font-weight: bold;
                    }
                    .similarity-medium {
                        background-color: #f39c12;
                        color: white;
                        padding: 4px 8px;
                        border-radius: 4px;
                        font-weight: bold;
                    }
                    .similarity-low {
                        background-color: #27ae60;
                        color: white;
                        padding: 4px 8px;
                        border-radius: 4px;
                        font-weight: bold;
                    }
                    .status-review {
                        color: #e74c3c;
                        font-weight: bold;
                    }
                    .status-monitor {
                        color: #f39c12;
                        font-weight: bold;
                    }
                    .status-normal {
                        color: #27ae60;
                        font-weight: bold;
                    }
                """)
        
        with tag('body'):
            # Header section
            with tag('div', klass='header'):
                with tag('h1'):
                    text('Student Work Similarity Analysis')
                with tag('p'):
                    text(f'Generated on: {datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S")}')
            
            # Summary section
            high_similarity = len([x for x in similarity_data if x['similarity'] > 80])
            medium_similarity = len([x for x in similarity_data if 50 < x['similarity'] <= 80])
            
            with tag('div', klass='summary'):
                with tag('h2'):
                    text('Summary')
                with tag('p'):
                    text(f'Total comparisons analyzed: {len(similarity_data)}')
                with tag('p'):
                    text(f'High similarity cases (>80%): {high_similarity}')
                with tag('p'):
                    text(f'Medium similarity cases (50-80%): {medium_similarity}')
                with tag('p'):
                    text(f'Low similarity cases (<50%): {len(similarity_data) - high_similarity - medium_similarity}')
            
            # Table section
            with tag('div', klass='table-container'):
                with tag('table'):
                    # Table header
                    with tag('thead'):
                        with tag('tr'):
                            with tag('th'):
                                text('Student 1')
                            with tag('th'):
                                text('Student 2')
                            with tag('th'):
                                text('Similarity %')
                            with tag('th'):
                                text('Status')
                            with tag('th'):
                                text('Action Needed')
                    
                    # Table body
                    with tag('tbody'):
                        for item in similarity_data:
                            similarity = item['similarity']
                            
                            # Determine styling and status
                            if similarity > 80:
                                sim_class = 'similarity-high'
                                status_class = 'status-review'
                                status_text = 'Review Required'
                                action_text = 'Investigate for plagiarism'
                            elif similarity > 50:
                                sim_class = 'similarity-medium'
                                status_class = 'status-monitor'
                                status_text = 'Monitor'
                                action_text = 'Check for common sources'
                            else:
                                sim_class = 'similarity-low'
                                status_class = 'status-normal'
                                status_text = 'Normal'
                                action_text = 'No action needed'
                            
                            with tag('tr'):
                                with tag('td'):
                                    text(item['student1'])
                                with tag('td'):
                                    text(item['student2'])
                                with tag('td'):
                                    with tag('span', klass=sim_class):
                                        text(f'{similarity:.1f}%')
                                with tag('td', klass=status_class):
                                    text(status_text)
                                with tag('td'):
                                    text(action_text)
    
    return doc.getvalue()

# Usage example
similarity_data = [
    {'student1': 'Alice Johnson', 'student2': 'Bob Smith', 'similarity': 85.2},
    {'student1': 'Carol White', 'student2': 'Dave Brown', 'similarity': 45.1},
    {'student1': 'Eve Wilson', 'student2': 'Frank Miller', 'similarity': 92.8},
    {'student1': 'Grace Lee', 'student2': 'Henry Davis', 'similarity': 23.5},
]

# Generate and save the report
html_report = generate_similarity_report(similarity_data)

with open('similarity_report.html', 'w') as f:
    f.write(html_report)

print("Report generated: similarity_report.html")
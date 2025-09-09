from flask import Flask, request, render_template, redirect, url_for, session, make_response
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import os
import random

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-me-please")
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=0)  # disable static cache during dev

# ======== Quiz questions ========
QUESTIONS = [
  {
    "id": 1,
    "question": "What does deployment mean in software development?",
    "options": ["Writing code locally", "Putting an app live on the internet", "Testing code", "Designing user interfaces"],
    "answer": 1
  },
  {
    "id": 2,
    "question": "Why is deployment important?",
    "options": ["It hides code", "It lets clients and users access your work online", "It replaces coding", "It removes the need for testing"],
    "answer": 1
  },
  {
    "id": 3,
    "question": "Which of the following is NOT a reason to avoid deploying immediately after programming?",
    "options": ["Bugs may exist", "Security issues may appear", "User experience may be poor", "Code runs faster locally"],
    "answer": 3
  },
  {
    "id": 4,
    "question": "What does ITIL stand for?",
    "options": ["Information Technology Infrastructure Library", "Internet Technology Integration Layer", "Internal Testing Infrastructure Language", "Information Technology Innovation Lab"],
    "answer": 0
  },
  {
    "id": 5,
    "question": "In ITIL, what is an 'Incident'?",
    "options": ["A planned system upgrade", "A request for new software", "Something that breaks, like a printer not working", "The root cause of a bug"],
    "answer": 2
  },
  {
    "id": 6,
    "question": "Who is the first point of contact for IT issues in ITIL?",
    "options": ["Incident Manager", "Problem Manager", "Service Desk Agent", "Change Manager"],
    "answer": 2
  },
  {
    "id": 7,
    "question": "Which ITIL role is responsible for approving and managing system changes?",
    "options": ["Incident Manager", "Problem Manager", "Change Manager", "Service Desk Agent"],
    "answer": 2
  },
  {
    "id": 8,
    "question": "What does DevOps stand for?",
    "options": ["Development + Operations", "Device + Optimization", "Deployment + Options", "Design + Operations"],
    "answer": 0
  },
  {
    "id": 9,
    "question": "What problem does DevOps primarily solve?",
    "options": ["Bug fixing", "Lack of programming skills", "Disconnect between developers and operations", "Database scaling"],
    "answer": 2
  },
  {
    "id": 10,
    "question": "Which of the following is a key benefit of DevOps?",
    "options": ["More silos between teams", "Slower releases", "Faster collaboration and deployment", "Increased documentation overhead"],
    "answer": 2
  },
  {
    "id": 11,
    "question": "Which stage in the DevOps lifecycle involves writing code collaboratively?",
    "options": ["Plan", "Develop", "Build", "Release"],
    "answer": 1
  },
  {
    "id": 12,
    "question": "Which stage in the DevOps lifecycle uses tools like Jenkins and Kubernetes?",
    "options": ["Develop", "Build", "Deploy", "Monitor"],
    "answer": 2
  },
  {
    "id": 13,
    "question": "What does a hypervisor do in virtualization?",
    "options": ["Runs containers", "Allocates CPU, memory, and storage to virtual machines", "Hosts websites", "Manages databases"],
    "answer": 1
  },
  {
    "id": 14,
    "question": "How is containerization different from virtualization?",
    "options": ["Containers require separate OS, VMs share one OS", "Containers share the host OS kernel, VMs run full OS", "Containers cannot run apps", "VMs are faster than containers"],
    "answer": 1
  },
  {
    "id": 15,
    "question": "What is Git primarily used for?",
    "options": ["Database management", "Version control", "Cloud hosting", "Code compilation"],
    "answer": 1
  },
  {
    "id": 16,
    "question": "What does a Git commit represent?",
    "options": ["A snapshot of changes", "A new branch", "A merge conflict", "A deployment"],
    "answer": 0
  },
  {
    "id": 17,
    "question": "Which of the following is a popular Linux distribution?",
    "options": ["Windows", "Fedora", "iOS", "Solaris"],
    "answer": 1
  },
  {
    "id": 18,
    "question": "What are the three layers in a three-tier architecture?",
    "options": ["Data, Cloud, Virtualization", "Frontend, Middleware, Database", "Linux, Windows, Mac", "User, Server, Network"],
    "answer": 1
  },
  {
    "id": 19,
    "question": "Which of the following is a benefit of Infrastructure as Code (IaC)?",
    "options": ["Manual configuration", "Automation and consistency", "Slower deployment", "Higher error rate"],
    "answer": 1
  },
  {
    "id": 20,
    "question": "What is Ansible mainly used for?",
    "options": ["Cloud storage", "Configuration management and automation", "Version control", "Monitoring applications"],
    "answer": 1
  }
]


# ======== Helpers for certificate rendering ========
def _font(path_candidates, size):
    for p in path_candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size=size)
    # fallback to PIL default if nothing found
    return ImageFont.load_default()

# adjust to your deployed font locations as needed
FONT_BOLD_CANDIDATES = [
    os.path.join('static', 'fonts', 'DejaVuSans-Bold.ttf'),
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
]
FONT_REG_CANDIDATES = [
    os.path.join('static', 'fonts', 'DejaVuSans.ttf'),
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
]

def build_certificate_image(name: str, date_str: str) -> Image.Image:
    bg_path = os.path.join(app.static_folder, 'certificate_bg.png')
    im = Image.open(bg_path).convert('RGBA')
    w, h = im.size
    draw = ImageDraw.Draw(im)

    name = name.upper().strip()
    max_name_width = int(w * 0.72)
    size = 80
    while size >= 80:
        f_try = _font(FONT_BOLD_CANDIDATES, size)
        bbox = draw.textbbox((0, 0), name, font=f_try)
        if (bbox[2] - bbox[0]) <= max_name_width:
            font_name = f_try
            break
        size -= 4
    else:
        font_name = _font(FONT_BOLD_CANDIDATES, 60)

    font_date = _font(FONT_REG_CANDIDATES, 56)

    name_x = w // 2
    name_y = int(h * 0.460)
    date_x = int(w * 0.130)
    date_y = int(h * 0.750)

    draw.text((name_x, name_y), name, fill=(0, 0, 0), font=font_name, anchor='mm')
    draw.text((date_x, date_y), date_str, fill=(0, 0, 0), font=font_date, anchor='lm')

    return im

def _image_bytes(name: str, date_str: str) -> bytes:
    img = build_certificate_image(name, date_str)
    buf = BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

# ======== Routes ========
@app.route("/", methods=["GET", "POST"])
def capture_name():
    if request.method == "POST":
        name = request.form.get("participant_name", "").strip()
        if not name:
            return render_template("name.html", error="Please enter your name.")
        session["participant_name"] = name

        # Create a randomized quiz order for this participant
        randomized = QUESTIONS[:]
        random.shuffle(randomized)
        session["quiz_questions"] = randomized

        return redirect(url_for("quiz"))
    return render_template("name.html")

@app.route("/quiz")
def quiz():
    if "participant_name" not in session:
        return redirect(url_for("capture_name"))

    questions = session.get("quiz_questions", QUESTIONS)
    return render_template("quiz.html", questions=questions)

@app.route("/submit", methods=["POST"])
def submit():
    if "participant_name" not in session:
        return redirect(url_for("capture_name"))

    questions = session.get("quiz_questions", QUESTIONS)
    score = 0
    total = len(questions)
    incorrect_answers = []

    for q in questions:
        ans = request.form.get(f"q{q['id']}")
        if ans is not None and ans.isdigit():
            submitted = int(ans)
            if submitted == q['answer']:
                score += 1
            else:
                incorrect_answers.append({
                    "question": q['question'],
                    "correct": q['options'][q['answer']],
                    "yours": q['options'][submitted]
                })

    participant_name = session["participant_name"]
    today_str = datetime.today().strftime("%d.%m.%Y")

    return render_template(
        "results.html",
        name=participant_name,
        date_str=today_str,
        score=score,
        total=total,
        incorrect_answers=incorrect_answers
    )

@app.route("/certificate-image")
def certificate_image():
    name = request.args.get("name", "STUDENT")
    date_str = request.args.get("date", datetime.today().strftime("%d.%m.%Y"))
    download = request.args.get("download")

    data = _image_bytes(name, date_str)
    resp = make_response(data)
    resp.mimetype = "image/png"
    if download:
        resp.headers["Content-Disposition"] = f'attachment; filename="certificate_{name}.png"'
    return resp

@app.route("/certificate-pdf")
def certificate_pdf():
    name = request.args.get("name", "STUDENT")
    date_str = request.args.get("date", datetime.today().strftime("%d.%m.%Y"))

    img_data = _image_bytes(name, date_str)
    img = Image.open(BytesIO(img_data)).convert("RGB")

    buf = BytesIO()
    img.save(buf, format="PDF", resolution=300)
    pdf_bytes = buf.getvalue()

    resp = make_response(pdf_bytes)
    resp.mimetype = "application/pdf"
    resp.headers["Content-Disposition"] = f'attachment; filename="certificate_{name}.pdf"'
    return resp

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)

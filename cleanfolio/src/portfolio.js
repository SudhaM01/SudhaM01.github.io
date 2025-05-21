const header = {
  // all the properties are optional - can be left empty or deleted
  homepage: 'https://SudhaM01.github.io/cleanfolio-main',
  title: 'Portfolio',
}

const about = {
  // all the properties are optional - can be left empty or deleted
  name: 'Sudha Muppala',
  role: 'AI Engineer | Cybersecurity Analyst',
  description:
    ' Master’s in Artificial Intelligence from Monash University with expertise in Machine Learning, Reinforcement Learning, and NLP. Former Cybersecurity Analyst at Wipro. Passionate about using AI to drive innovative solutions.',
  resume: 'https://example.com',
  social: {
    linkedin: 'https://www.linkedin.com/in/sudha-muppala-323922174/',
    github: 'https://github.com/SudhaM01/SudhaM01.github.io',
  },
}

const projects = [
  // projects can be added an removed
  // if there are no projects, Projects section won't show up
  {
    name: 'MRI Tumor Classification with CNN',
    description:
      'Built and optimized CNNs to detect tumors from MRI scans, achieving high precision through data augmentation and layer tuning ',
    stack: ['TensorFlow', 'NumPy', 'CNN'],
    sourceCode: 'https://github.com/SudhaM01/SudhaM01.github.io/blob/main/Brain_tumor.ipynb'
  },
    {
    name: 'Object Detection for Construction Worker Safety',
    description:
      'Developed an Object Detection model to recognize safety equipment (helmets, safety vests, masks) worn by workers in construction sites using YOLO (You Only Look Once) and Faster R-CNN.',
    stack: ['Deep Learning', 'YOLO', 'R-CNN'],
    sourceCode: 'https://github.com'

  },
  {
    name: 'Recipe Generator using Attention Mechanism',
    description:
      'Implemented a seq2seq architecture with attention to create human-readable recipes from ingredient lists ',
    stack: ['PyTorch', 'NLP', 'Seq2seq architecture'],
    sourceCode: 'https://github.com/SudhaM01/SudhaM01.github.io/blob/main/Machine_Translation_model_NLP.ipynb'

  },

]

const skills = [
  // skills can be added or removed
  // if there are no skills, Skills section won't show up
  'Python',
  'R',
  'Artificial Intelligence',
  'Machine Learning',
  'Deep Learning',
  'Data Analytics',
  'LLM',
  'Cybersecurity',
  'SQL',
  'Git',
  'CI/CD',
  'AWS',
  'RAG',
]

const contact = {
  // email is optional - if left empty Contact section won't show up
  email: 'muppalasudha@gmail.com',
}

export { header, about, projects, skills, contact }

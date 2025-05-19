const header = {
  // all the properties are optional - can be left empty or deleted
  homepage: 'https://SudhaM01.github.io/cleanfolio-main',
  title: 'JS.',
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
    github: 'https://github.com',
  },
}

const projects = [
  // projects can be added an removed
  // if there are no projects, Projects section won't show up
  {
    name: 'Project 1',
    description:
      'Amet asperiores et impedit aliquam consectetur? Voluptates sed a nulla ipsa officia et esse aliquam',
    stack: ['SASS', 'TypeScript', 'React'],
    sourceCode: 'https://github.com',
    livePreview: 'https://github.com',
  },
  {
    name: 'Project 2',
    description:
      'Amet asperiores et impedit aliquam consectetur? Voluptates sed a nulla ipsa officia et esse aliquam',
    stack: ['SASS', 'TypeScript', 'React'],
    sourceCode: 'https://github.com',
    livePreview: 'https://github.com',
  },
  {
    name: 'Project 3',
    description:
      'Amet asperiores et impedit aliquam consectetur? Voluptates sed a nulla ipsa officia et esse aliquam',
    stack: ['SASS', 'TypeScript', 'React'],
    sourceCode: 'https://github.com',
    livePreview: 'https://github.com',
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

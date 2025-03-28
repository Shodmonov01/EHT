export interface Question {
    id: number;
    text: string;
    image?: string;
    answers: Answer[];
  }
  export interface Answer {
    id: number;
    text: string;
  }
  
  export interface Category {
    name: string;
    questions: Question[];
  }
  export interface ResultProps {
    correctQuestions: number;
    totalQuestions: number;
    percentageScore: number;
    quizName: string;
    quizResultId: string;
  }
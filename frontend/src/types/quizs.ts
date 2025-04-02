export interface Question {
  id: number;
  text: string;
  category: string;
  subcategory: string;
  image?: string | null;
  answers: Answer[];
}

export interface Answer {
  id: number;
  text: string;
  image: string;
}

export interface Category {
  id: number;
  name: string;
  formatted_categories: string;
}

export interface ResultProps {
  correctQuestions: number;
  totalQuestions: number;
  percentageScore: number;
  quizName: string;
  quizResultId: string;
}

export interface QuizStartRequest {
  name: string;
  parents_fullname: string;
  phone_number: string;
  category_set_id: number;
  is_agreed: boolean;
}

export interface QuizResult {
  token: string;
  category_set_id: string;
}

export interface CategoryQuestions {
  category_id: number;
  category_name: string;
  questions: Question[];
}

export interface QuizSubmitRequest {
  answers: { [key: number]: number };
}

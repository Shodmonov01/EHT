import axios from "axios";
import {
  QuizResult,
  QuizStartRequest,
  Category,
  CategoryQuestions,
  QuizSubmitRequest,
} from "../types/quizs";

const API_URL = "http://45.66.10.106:8000";

const axiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
    "Accept-Language": "ru",
  },
});

export const fetchCategories = async () => {
  const { data } = await axiosInstance.get<Category[]>(
    `/quiz/api/category-set/`
  );
  return data;
};

export const startQuiz = async (quizData: QuizStartRequest) => {
  const { data } = await axiosInstance.post<QuizResult>(
    `/quiz/api/quizzes/start`,
    quizData
  );
  return data;
};

export const fetchQuestions = async (categorySetId: number) => {
  const { data } = await axiosInstance.get<CategoryQuestions[]>(
    `/quiz/api/quiz/questions/${categorySetId}/`
  );
  return data;
};

export const submitQuiz = async (answers: QuizSubmitRequest) => {
  const { data } = await axiosInstance.post(`/quiz/api/quiz/submit/`, answers);
  return data;
};

export const getQuizResultById = async (id: number) => {
  const { data } = await axiosInstance.get<QuizResult>(
    `/quiz/api/quizzes/quiz-results/${id}/`
  );
  return data;
};

export const categoryKeys = {
  all: ["categories"] as const,
};

export const quizKeys = {
  all: ["quizzes"] as const,
  start: () => [...quizKeys.all, "start"] as const,
};

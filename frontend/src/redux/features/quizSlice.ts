import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface QuizState {
  token: string | null;
  category_set_id: number | null;
}

const initialState: QuizState = {
  token: null,
  category_set_id: null,
};

const quizSlice = createSlice({
  name: 'quiz',
  initialState,
  reducers: {
    setQuizData: (state, action: PayloadAction<{ token: string; category_set_id: string }>) => {
      state.token = action.payload.token;
      state.category_set_id = Number(action.payload.category_set_id);
    },
    resetQuizData: (state) => {
      state.token = null;
      state.category_set_id = null;
    },
  },
});

export const { setQuizData, resetQuizData } = quizSlice.actions;
export default quizSlice.reducer; 
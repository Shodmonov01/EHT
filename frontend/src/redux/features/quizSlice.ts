import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface QuizState {
  token: string | null;
  categorySetId: string | null;
}

const initialState: QuizState = {
  token: null,
  categorySetId: null,
};

const quizSlice = createSlice({
  name: 'quiz',
  initialState,
  reducers: {
    setQuizData: (state, action: PayloadAction<{ token: string; category_set_id: string }>) => {
      state.token = action.payload.token;
      state.categorySetId = action.payload.category_set_id;
    },
    resetQuizData: (state) => {
      state.token = null;
      state.categorySetId = null;
    },
  },
});

export const { setQuizData, resetQuizData } = quizSlice.actions;
export default quizSlice.reducer; 
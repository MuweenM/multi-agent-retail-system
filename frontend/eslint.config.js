import js from '@eslint/js';
import globals from 'globals';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import tseslint from 'typescript-eslint';
import react from 'eslint-plugin-react';

export default tseslint.config(
  { ignores: ['dist'] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
      react,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': [
        'warn',
        { allowConstantExport: true },
      ],
    },
  },
  {
    files: ['src/components/app/**/*.{ts,tsx}', 'src/App.tsx'],
    rules: {
      'react/forbid-elements': [
        'error',
        {
          forbid: [
            {
              element: 'button',
              message:
                'Design system constraint: Use <Button> from @/components/ui/button instead of raw <button>.',
            },
            {
              element: 'input',
              message:
                'Design system constraint: Use <Input> from @/components/ui/input instead of raw <input>.',
            },
            {
              element: 'kbd',
              message:
                'Design system constraint: Use <Kbd> from @/components/ui/kbd instead of raw <kbd>.',
            },
            {
              element: 'textarea',
              message:
                'Design system constraint: Use <Textarea> from @/components/ui/textarea instead of raw <textarea>.',
            },
            {
              element: 'select',
              message:
                'Design system constraint: Use <Select> from @/components/ui/select instead of raw <select>.',
            },
          ],
        },
      ],
    },
  },
  {
    files: ['src/components/ui/**/*.{ts,tsx}'],
    rules: {
      'react-refresh/only-export-components': 'off',
      'react-hooks/set-state-in-effect': 'off',
    },
  }
);

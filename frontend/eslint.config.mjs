import js from '@eslint/js';
import globals from 'globals';

export default [
  { ignores: ['node_modules/**', '.vercel/**', 'coverage/**'] },
  js.configs.recommended,
  {
    files: ['**/*.js', '**/*.mjs'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: { ...globals.browser, ...globals.node },
    },
    rules: {
      'no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
      eqeqeq: 'error',
      'no-eval': 'error',
      'no-implied-eval': 'error',
      'no-new-func': 'error',
      'no-console': 'error',
      'no-restricted-properties': [
        'error',
        {
          property: 'innerHTML',
          message: 'Construct literal text with the DOM builder.',
        },
        { property: 'outerHTML', message: 'Construct nodes with the DOM builder.' },
        {
          object: 'document',
          property: 'write',
          message: 'Construct nodes with the DOM builder.',
        },
      ],
      curly: ['error', 'multi-line'],
      complexity: ['error', 8],
      'max-lines': ['error', { max: 250 }],
      'max-lines-per-function': ['error', { max: 35 }],
      'max-depth': ['error', 3],
    },
  },
];

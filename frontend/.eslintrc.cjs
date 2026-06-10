// .eslintrc.cjs
module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs'],
  parser: '@typescript-eslint/parser',
  plugins: ['react-refresh', 'security'],
  rules: {
    'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
    'security/detect-object-injection': 'warn',
    'security/detect-eval-with-expression': 'error',
    // ... 其他规则
  },
};
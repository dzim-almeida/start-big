import type { Meta, StoryObj } from '@storybook/vue3';
import BaseInput from './BaseInput.vue';

const meta: Meta<typeof BaseInput> = {
  title: 'Components/BaseInput',
  component: BaseInput,
  argTypes: {
    type: {
      control: 'select',
      options: ['text', 'email', 'password', 'number', 'tel'],
    },
    modelValue: {
      control: 'text',
    },
    label: {
      control: 'text',
    },
    placeholder: {
      control: 'text',
    },
    error: {
      control: 'text',
    },
    disabled: {
      control: 'boolean',
    },
  },
};

export default meta;
type Story = StoryObj<typeof BaseInput>;

export const Default: Story = {
  args: {
    type: 'text',
    label: 'Nome',
    placeholder: 'Digite seu nome',
    modelValue: '',
    disabled: false,
    error: '',
  },
};

export const WithValue: Story = {
  args: {
    type: 'text',
    label: 'Nome',
    placeholder: 'Digite seu nome',
    modelValue: 'João Silva',
    disabled: false,
    error: '',
  },
};

export const Email: Story = {
  args: {
    type: 'email',
    label: 'E-mail',
    placeholder: 'exemplo@email.com',
    modelValue: '',
    disabled: false,
    error: '',
  },
};

export const Password: Story = {
  args: {
    type: 'password',
    label: 'Senha',
    placeholder: 'Digite sua senha',
    modelValue: '',
    disabled: false,
    error: '',
  },
};

export const Number: Story = {
  args: {
    type: 'number',
    label: 'Quantidade',
    placeholder: '0',
    modelValue: '',
    disabled: false,
    error: '',
  },
};

export const Tel: Story = {
  args: {
    type: 'tel',
    label: 'Telefone',
    placeholder: '(00) 00000-0000',
    modelValue: '',
    disabled: false,
    error: '',
  },
};

export const WithError: Story = {
  args: {
    type: 'email',
    label: 'E-mail',
    placeholder: 'exemplo@email.com',
    modelValue: 'email-invalido',
    disabled: false,
    error: 'Por favor, insira um e-mail válido',
  },
};

export const Disabled: Story = {
  args: {
    type: 'text',
    label: 'Campo desabilitado',
    placeholder: 'Não é possível editar',
    modelValue: 'Valor fixo',
    disabled: true,
    error: '',
  },
};

export const WithoutLabel: Story = {
  args: {
    type: 'text',
    label: '',
    placeholder: 'Input sem label',
    modelValue: '',
    disabled: false,
    error: '',
  },
};
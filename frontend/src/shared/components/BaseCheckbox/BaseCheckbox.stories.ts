import type { Meta, StoryObj } from '@storybook/vue3';
import BaseCheckbox from './BaseCheckbox.vue';

const meta: Meta<typeof BaseCheckbox> = {
  title: 'Components/BaseCheckbox',
  component: BaseCheckbox,
  argTypes: {
    modelValue: {
      control: 'boolean',
    },
    label: {
      control: 'text',
    },
    disabled: {
      control: 'boolean',
    },
  },
};

export default meta;
type Story = StoryObj<typeof BaseCheckbox>;

export const Default: Story = {
  args: {
    modelValue: false,
    label: 'Aceito os termos de uso',
    disabled: false,
  },
};

export const Checked: Story = {
  args: {
    modelValue: true,
    label: 'Aceito os termos de uso',
    disabled: false,
  },
};

export const Disabled: Story = {
  args: {
    modelValue: false,
    label: 'Opção desabilitada',
    disabled: true,
  },
};

export const DisabledChecked: Story = {
  args: {
    modelValue: true,
    label: 'Opção desabilitada marcada',
    disabled: true,
  },
};

export const WithoutLabel: Story = {
  args: {
    modelValue: false,
    label: '',
    disabled: false,
  },
};

export const LongLabel: Story = {
  args: {
    modelValue: false,
    label: 'Li e concordo com os termos de uso e política de privacidade da plataforma',
    disabled: false,
  },
};
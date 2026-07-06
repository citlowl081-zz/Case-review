import React, { useState } from 'react';
import { Form, Input, Button, Card, Typography, message, Divider } from 'antd';
import { useAuthStore } from '../../store/authStore';
import { useThemeStore } from '../../store/themeStore';
import { useAuth } from '../../hooks/useAuth';
import ThemeToggle from '../../components/ThemeToggle';

const { Title } = Typography;

export default function Settings() {
  const { user } = useAuth();
  const changePassword = useAuthStore((s) => s.changePassword);
  const [loading, setLoading] = useState(false);

  const onChangePassword = async (values: {
    old_password: string;
    new_password: string;
    confirm_password: string;
  }) => {
    if (values.new_password !== values.confirm_password) {
      message.error('两次输入的新密码不一致');
      return;
    }
    setLoading(true);
    try {
      await changePassword(
        values.old_password,
        values.new_password,
        values.confirm_password
      );
      message.success('密码修改成功');
    } catch (err: any) {
      message.error(err?.response?.data?.detail || '密码修改失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 600, margin: '24px auto', padding: '0 16px' }}>
      <Card title="个人设置">
        <div style={{ marginBottom: 16 }}>
          <strong>用户名：</strong>
          {user?.username}
        </div>
        <div style={{ marginBottom: 16 }}>
          <strong>角色：</strong>
          {user?.role === 'admin' ? '管理员' : '普通用户'}
        </div>

        <Divider />

        <Title level={5}>修改密码</Title>
        <Form layout="vertical" onFinish={onChangePassword}>
          <Form.Item
            name="old_password"
            label="旧密码"
            rules={[{ required: true, message: '请输入旧密码' }]}
          >
            <Input.Password />
          </Form.Item>
          <Form.Item
            name="new_password"
            label="新密码"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 6, message: '密码至少6个字符' },
            ]}
          >
            <Input.Password />
          </Form.Item>
          <Form.Item
            name="confirm_password"
            label="确认新密码"
            rules={[{ required: true, message: '请确认新密码' }]}
          >
            <Input.Password />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>
            修改密码
          </Button>
        </Form>

        <Divider />

        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <strong>主题切换：</strong>
          <ThemeToggle />
        </div>
      </Card>
    </div>
  );
}

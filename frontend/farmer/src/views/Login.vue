<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-logo">
        <div class="logo-icon"><Wheat :size="16" /></div>
        <h1>AgriSpatial 农业遥感数据平台</h1>
        <p class="auth-subtitle">农户端 · 登录</p>
      </div>
      <!-- 第一步：用户名密码 -->
      <form v-if="!pending2FA" class="auth-form" @submit.prevent="handleLogin">
        <div class="form-field">
          <label>用户名</label>
          <input v-model="form.username" type="text" placeholder="请输入用户名" autocomplete="username" />
        </div>
        <div class="form-field">
          <label>密码</label>
          <div class="pwd-wrap">
            <input v-model="form.password" :type="showPwd ? 'text' : 'password'" placeholder="请输入密码" autocomplete="current-password" />
            <button type="button" class="pwd-eye" @click="showPwd = !showPwd">
              <EyeOff v-if="!showPwd" :size="16" /><Eye v-else :size="16" />
            </button>
          </div>
        </div>
        <div class="form-row">
          <label class="check-label"><input type="checkbox" v-model="remember" /> 记住我</label>
          <a class="forgot-link" href="#" @click.prevent="showForgot = true">忘记密码？</a>
        </div>
        <p class="auth-error" v-if="error">{{ error }}</p>
        <button type="submit" class="btn btn-primary btn-lg btn-block" :disabled="loading">
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>

      <!-- 第二步：两步验证 -->
      <form v-else class="auth-form" @submit.prevent="handleVerify2FA">
        <div class="twofa-info">
          <ShieldCheck :size="32" />
          <p>验证码已发送至 <strong>{{ phoneHint }}</strong></p>
          <p class="twofa-hint">请查看后端控制台获取验证码（开发模式）</p>
        </div>
        <div class="form-field">
          <label>验证码</label>
          <input v-model="verifyCode" type="text" placeholder="请输入 6 位验证码" maxlength="6" autocomplete="one-time-code" />
        </div>
        <p class="auth-error" v-if="error">{{ error }}</p>
        <button type="submit" class="btn btn-primary btn-lg btn-block" :disabled="loading">
          {{ loading ? '验证中...' : '验证' }}
        </button>
        <button type="button" class="btn-back" @click="pending2FA = false">返回重新登录</button>
      </form>
      <p class="auth-link">还没有账号？<router-link to="/register">立即注册</router-link></p>
    </div>

    <!-- 忘记密码弹窗 -->
    <div v-if="showForgot" class="modal-overlay" @click.self="showForgot = false">
      <div class="modal-box">
        <div class="modal-head">
          <h3>重置密码</h3>
          <button class="modal-close" @click="showForgot = false"><X :size="18" /></button>
        </div>
        <div class="modal-body">
          <!-- 步骤1：输入手机号 -->
          <form v-if="forgotStep === 1" class="auth-form" @submit.prevent="sendResetCode">
            <div class="form-field">
              <label>注册手机号</label>
              <input v-model="forgotPhone" type="text" placeholder="请输入注册时的手机号" maxlength="11" />
            </div>
            <p class="auth-error" v-if="forgotError">{{ forgotError }}</p>
            <button type="submit" class="btn btn-primary btn-lg btn-block" :disabled="forgotLoading">
              {{ forgotLoading ? '发送中...' : '发送验证码' }}
            </button>
          </form>
          <!-- 步骤2：输入验证码和新密码 -->
          <form v-else class="auth-form" @submit.prevent="handleResetPassword">
            <div class="twofa-info">
              <ShieldCheck :size="28" />
              <p>验证码已发送至 <strong>{{ forgotPhone }}</strong></p>
              <p class="twofa-hint">请查看后端控制台获取验证码（开发模式）</p>
            </div>
            <div class="form-field">
              <label>验证码</label>
              <input v-model="forgotCode" type="text" placeholder="6 位验证码" maxlength="6" />
            </div>
            <div class="form-field">
              <label>新密码</label>
              <input v-model="forgotNewPwd" type="password" placeholder="至少 6 位" />
            </div>
            <p class="auth-error" v-if="forgotError">{{ forgotError }}</p>
            <button type="submit" class="btn btn-primary btn-lg btn-block" :disabled="forgotLoading">
              {{ forgotLoading ? '重置中...' : '重置密码' }}
            </button>
            <button type="button" class="btn-back" @click="forgotStep = 1">返回重新输入手机号</button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import { useAuth } from '../composables/useAuth'
import { Wheat, Eye, EyeOff, ShieldCheck, X } from 'lucide-vue-next'

const router = useRouter()
const { login, verify2FA } = useAuth()
const form = ref({ username: '', password: '' })
const loading = ref(false)
const error = ref('')
const showPwd = ref(false)
const remember = ref(false)

// 两步验证状态
const pending2FA = ref(false)
const tempToken = ref('')
const phoneHint = ref('')
const verifyCode = ref('')

// 忘记密码状态
const showForgot = ref(false)
const forgotStep = ref(1)
const forgotPhone = ref('')
const forgotCode = ref('')
const forgotNewPwd = ref('')
const forgotLoading = ref(false)
const forgotError = ref('')

async function handleLogin() {
  loading.value = true; error.value = ''
  try {
    const data = await login(form.value.username, form.value.password)
    if (data.need_2fa) {
      pending2FA.value = true
      tempToken.value = data.temp_token
      phoneHint.value = data.phone_hint
    } else {
      router.push('/')
    }
  } catch (e) {
    error.value = '用户名或密码错误'
  } finally {
    loading.value = false
  }
}

async function handleVerify2FA() {
  loading.value = true; error.value = ''
  try {
    await verify2FA(tempToken.value, verifyCode.value)
    router.push('/')
  } catch (e) {
    error.value = '验证码错误或已过期'
  } finally {
    loading.value = false
  }
}

async function sendResetCode() {
  if (!forgotPhone.value || forgotPhone.value.length < 11) { forgotError.value = '请输入正确的手机号'; return }
  forgotLoading.value = true; forgotError.value = ''
  try {
    await api.post('/auth/forgot-password', { phone: forgotPhone.value })
    forgotStep.value = 2
  } catch (e) {
    forgotError.value = e.response?.data?.detail || '发送失败'
  } finally {
    forgotLoading.value = false
  }
}

async function handleResetPassword() {
  if (!forgotCode.value) { forgotError.value = '请输入验证码'; return }
  if (forgotNewPwd.value.length < 6) { forgotError.value = '密码至少6位'; return }
  forgotLoading.value = true; forgotError.value = ''
  try {
    await api.post('/auth/reset-password', { phone: forgotPhone.value, code: forgotCode.value, new_password: forgotNewPwd.value })
    showForgot.value = false
    forgotStep.value = 1
    forgotPhone.value = ''; forgotCode.value = ''; forgotNewPwd.value = ''
    error.value = ''
    alert('密码重置成功，请使用新密码登录')
  } catch (e) {
    forgotError.value = e.response?.data?.detail || '重置失败'
  } finally {
    forgotLoading.value = false
  }
}
</script>

<style scoped>
@import '../styles/auth.css';
.pwd-wrap { position: relative; }
.pwd-wrap input { padding-right: 40px; }
.pwd-eye {
  position: absolute; right: 10px; top: 50%; transform: translateY(-50%);
  background: none; border: none; color: #999; cursor: pointer; padding: 4px;
}
.pwd-eye:hover { color: #333; }
.form-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-4); }
.check-label { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #666; cursor: pointer; }
.check-label input { width: auto; accent-color: #16a34a; }
.forgot-link { font-size: 13px; color: #16a34a; text-decoration: none; }
.forgot-link:hover { text-decoration: underline; }
.auth-logo .logo-icon {
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #22c55e, #16a34a);
  color: #fff; margin: 0 auto var(--space-4);
}
.twofa-info {
  text-align: center; margin-bottom: var(--space-4);
  color: #16a34a; display: flex; flex-direction: column; align-items: center; gap: 8px;
}
.twofa-info p { color: #333; font-size: 14px; margin: 0; }
.twofa-hint { color: #999; font-size: 12px; }
.btn-back {
  display: block; width: 100%; margin-top: 8px;
  background: none; border: none; color: #666; font-size: 13px;
  cursor: pointer; text-align: center; padding: 8px;
}
.btn-back:hover { color: #16a34a; }

/* 弹窗 */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center; z-index: 1000;
}
.modal-box {
  background: #fff; border-radius: 16px; width: 400px; max-width: 90vw;
  box-shadow: 0 20px 60px rgba(0,0,0,0.2);
}
.modal-head {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px; border-bottom: 1px solid #f0f0f0;
}
.modal-head h3 { font-size: 16px; font-weight: 700; color: #1a1a1a; }
.modal-close { background: none; border: none; color: #999; cursor: pointer; padding: 4px; }
.modal-close:hover { color: #333; }
.modal-body { padding: 24px 20px; }
</style>

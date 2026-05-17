<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-logo">
        <div class="logo-icon"><Wheat :size="16" /></div>
        <h1>注册账号</h1>
        <p class="auth-subtitle">加入 AgriSpatial 农业遥感数据平台</p>
      </div>
      <form class="auth-form" @submit.prevent="handleRegister">
        <div class="form-field">
          <label>用户名</label>
          <input v-model="form.username" type="text" placeholder="至少3个字符" />
        </div>
        <div class="form-field">
          <label>密码</label>
          <div class="pwd-wrap">
            <input v-model="form.password" :type="showPwd ? 'text' : 'password'" placeholder="至少6个字符" />
            <button type="button" class="pwd-eye" @click="showPwd = !showPwd">
              <EyeOff v-if="!showPwd" :size="16" /><Eye v-else :size="16" />
            </button>
          </div>
        </div>
        <div class="form-field">
          <label>手机号 <span style="color:var(--gis-text-dim);font-weight:400">（选填）</span></label>
          <input v-model="form.phone" type="text" placeholder="请输入手机号" />
        </div>
        <div class="form-field">
          <label>所在地区 <span style="color:var(--gis-text-dim);font-weight:400">（选填）</span></label>
          <input v-model="form.area" type="text" placeholder="如：黑龙江哈尔滨" />
        </div>
        <p class="auth-error" v-if="error">{{ error }}</p>
        <button type="submit" class="btn btn-primary btn-lg btn-block" :disabled="loading">
          {{ loading ? '注册中...' : '注册' }}
        </button>
      </form>
      <p class="auth-link">已有账号？<router-link to="/login">返回登录</router-link></p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'
import { Wheat, Eye, EyeOff } from 'lucide-vue-next'

const router = useRouter()
const { register } = useAuth()
const form = ref({ username: '', password: '', phone: '', area: '' })
const loading = ref(false)
const error = ref('')
const showPwd = ref(false)

async function handleRegister() {
  if (form.value.username.length < 3) { error.value = '用户名至少3个字符'; return }
  if (form.value.password.length < 6) { error.value = '密码至少6个字符'; return }
  loading.value = true; error.value = ''
  try {
    await register(form.value.username, form.value.password, form.value.phone, form.value.area)
    router.push('/')
  } catch (e) {
    error.value = '注册失败，用户名可能已存在'
  } finally {
    loading.value = false
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
</style>

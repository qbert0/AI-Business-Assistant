import type { StatItem } from '@/types/dashboard'

export const useDashboard = () => {
  const overview = computed<StatItem[]>(() => [
    { label: 'Tổ chức đang tham gia', value: '3', hint: '1 admin, 2 user' },
    { label: 'Tài liệu đã đồng bộ', value: '190+', hint: 'gồm file gốc và chunk đã index' },
    { label: 'Lượt hỏi nổi bật', value: '288', hint: 'nhóm câu hỏi về thu nhập chiếm tỷ trọng cao' }
  ])

  const suggestQuestions = computed(() => [
    'Thu nhập chịu thuế của em gồm các khoản nào?',
    'Mức thưởng quý của sales được tính ra sao?',
    'Quy trình xin xác nhận công tác thực hiện ở đâu?',
    'Nhân viên part-time có được tính KPI như full-time không?'
  ])

  return {
    overview,
    suggestQuestions
  }
}

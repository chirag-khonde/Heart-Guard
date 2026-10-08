import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../../services/api'
import Card from '../../components/common/Card'
import Input from '../../components/common/Input'
import Select from '../../components/common/Select'
import Button from '../../components/common/Button'
import PageHeader from '../../components/common/PageHeader'
import { User, Stethoscope, Heart, CheckCircle, ChevronLeft, ChevronRight } from 'lucide-react'
import { formatApiError } from '../../utils/errors'

const steps = [
  { id: 1, title: 'Personal Info', icon: User },
  { id: 2, title: 'Clinical Data', icon: Stethoscope },
  { id: 3, title: 'Lifestyle', icon: Heart },
  { id: 4, title: 'Review & Submit', icon: CheckCircle },
]

const chestPainTypes = [
  { value: 0, label: 'Typical Angina' },
  { value: 1, label: 'Atypical Angina' },
  { value: 2, label: 'Non-Anginal Pain' },
  { value: 3, label: 'Asymptomatic' },
]

const ecgOptions = [
  { value: 0, label: 'Normal' },
  { value: 1, label: 'ST-T Wave Abnormality' },
  { value: 2, label: 'Left Ventricular Hypertrophy' },
]

const sexOptions = [
  { value: 'male', label: 'Male' },
  { value: 'female', label: 'Female' },
]

export default function AssessmentPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState({})
  const [form, setForm] = useState({
    age: '',
    sex: '',
    chest_pain_type: '',
    resting_blood_pressure: '',
    cholesterol: '',
    fasting_blood_sugar: '',
    resting_ecg: '',
    max_heart_rate: '',
    exercise_induced_angina: '',
    st_depression: '',
    num_major_vessels: '',
    lifestyle_text: '',
  })

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  const validateStep = (s) => {
    const errs = {}
    if (s === 1) {
      if (!form.age || form.age < 1 || form.age > 120) errs.age = 'Enter a valid age (1-120)'
      if (!form.sex) errs.sex = 'Please select sex'
    }
    if (s === 2) {
      if (!form.chest_pain_type && form.chest_pain_type !== 0) errs.chest_pain_type = 'Required'
      if (!form.resting_blood_pressure) errs.resting_blood_pressure = 'Required'
      if (!form.cholesterol) errs.cholesterol = 'Required'
      if (!form.max_heart_rate) errs.max_heart_rate = 'Required'
      if (!form.resting_ecg && form.resting_ecg !== 0) errs.resting_ecg = 'Required'
      if (!form.st_depression && form.st_depression !== 0) errs.st_depression = 'Required'
      if (form.num_major_vessels === '' || form.num_major_vessels === null) errs.num_major_vessels = 'Required'
    }
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  const next = () => {
    if (validateStep(step)) setStep(step + 1)
  }

  const prev = () => setStep(step - 1)

  const handleSubmit = async () => {
    setLoading(true)
    try {
      const isMale = form.sex === 'male' || form.sex === '1' || form.sex === 1
      const clinicalData = {
        age: Number(form.age),
        sex: isMale ? 1 : 0,
        chest_pain_type: Number(form.chest_pain_type),
        resting_bp: Number(form.resting_blood_pressure),
        cholesterol: Number(form.cholesterol),
        fasting_blood_sugar: form.fasting_blood_sugar === 'true' || form.fasting_blood_sugar === true || form.fasting_blood_sugar === 1 ? 1 : 0,
        resting_ecg: Number(form.resting_ecg),
        max_heart_rate: Number(form.max_heart_rate),
        exercise_angina: form.exercise_induced_angina === 'true' || form.exercise_induced_angina === true || form.exercise_induced_angina === 1 ? 1 : 0,
        st_depression: Number(form.st_depression),
        num_major_vessels: Number(form.num_major_vessels),
      }
      const payload = {
        clinical_data: clinicalData,
        lifestyle_text: (form.lifestyle_text || '').trim() || 'No specific lifestyle risk factors reported.',
        ...clinicalData,
        resting_blood_pressure: clinicalData.resting_bp,
        exercise_induced_angina: clinicalData.exercise_angina,
      }
      const res = await api.assessments.create(payload)
      navigate('/assessment/result', { state: { assessment: res.data } })
    } catch (err) {
      setErrors({ submit: formatApiError(err, 'Assessment failed. Please try again.') })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto">
      <PageHeader title="Health Assessment" description="Complete the following to receive your heart disease risk assessment" />

      {/* Progress */}
      <div className="flex items-center justify-between mb-8">
        {steps.map((s, i) => (
          <div key={s.id} className="flex items-center">
            <div className={`flex items-center gap-2 ${step >= s.id ? 'text-red-600' : 'text-slate-400'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                step >= s.id ? 'bg-red-600 text-white' : 'bg-slate-200 text-slate-500'
              }`}>
                {step > s.id ? <CheckCircle className="h-4 w-4" /> : s.id}
              </div>
              <span className="hidden sm:block text-sm font-medium">{s.title}</span>
            </div>
            {i < steps.length - 1 && (
              <div className={`w-12 sm:w-20 h-0.5 mx-2 ${step > s.id ? 'bg-red-600' : 'bg-slate-200'}`} />
            )}
          </div>
        ))}
      </div>

      {errors.submit && (
        <div className="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg border border-red-200 mb-6">
          {errors.submit}
        </div>
      )}

      {/* Step 1: Personal */}
      {step === 1 && (
        <Card>
          <h3 className="text-lg font-semibold text-slate-900 mb-6">Personal Information</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <Input label="Age" type="number" value={form.age} onChange={update('age')} placeholder="e.g. 45" error={errors.age} />
            <Select label="Sex" value={form.sex} onChange={update('sex')} options={sexOptions} placeholder="Select..." error={errors.sex} />
          </div>
        </Card>
      )}

      {/* Step 2: Clinical */}
      {step === 2 && (
        <Card>
          <h3 className="text-lg font-semibold text-slate-900 mb-6">Clinical Measurements</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <Select label="Chest Pain Type" value={form.chest_pain_type} onChange={update('chest_pain_type')} options={chestPainTypes} placeholder="Select..." error={errors.chest_pain_type} />
            <Input label="Resting Blood Pressure (mmHg)" type="number" value={form.resting_blood_pressure} onChange={update('resting_blood_pressure')} placeholder="e.g. 120" error={errors.resting_blood_pressure} />
            <Input label="Cholesterol (mg/dl)" type="number" value={form.cholesterol} onChange={update('cholesterol')} placeholder="e.g. 200" error={errors.cholesterol} />
            <Select label="Fasting Blood Sugar > 120 mg/dl" value={form.fasting_blood_sugar} onChange={update('fasting_blood_sugar')} options={[{ value: 'true', label: 'Yes' }, { value: 'false', label: 'No' }]} placeholder="Select..." error={errors.fasting_blood_sugar} />
            <Select label="Resting ECG" value={form.resting_ecg} onChange={update('resting_ecg')} options={ecgOptions} placeholder="Select..." error={errors.resting_ecg} />
            <Input label="Max Heart Rate" type="number" value={form.max_heart_rate} onChange={update('max_heart_rate')} placeholder="e.g. 150" error={errors.max_heart_rate} />
            <Select label="Exercise Induced Angina" value={form.exercise_induced_angina} onChange={update('exercise_induced_angina')} options={[{ value: 'true', label: 'Yes' }, { value: 'false', label: 'No' }]} placeholder="Select..." error={errors.exercise_induced_angina} />
            <Input label="ST Depression (oldpeak)" type="number" step="0.1" value={form.st_depression} onChange={update('st_depression')} placeholder="e.g. 1.5" error={errors.st_depression} />
            <Select label="Number of Major Vessels (0-3)" value={form.num_major_vessels} onChange={update('num_major_vessels')} options={[{ value: '0', label: '0' }, { value: '1', label: '1' }, { value: '2', label: '2' }, { value: '3', label: '3' }]} placeholder="Select..." error={errors.num_major_vessels} />
          </div>
        </Card>
      )}

      {/* Step 3: Lifestyle */}
      {step === 3 && (
        <Card>
          <h3 className="text-lg font-semibold text-slate-900 mb-2">Lifestyle Information</h3>
          <p className="text-sm text-slate-500 mb-6">Describe your daily habits, diet, exercise, sleep, and stress levels</p>
          <textarea
            value={form.lifestyle_text}
            onChange={update('lifestyle_text')}
            rows={8}
            placeholder="e.g. I exercise 3 times a week, eat mostly vegetarian, sleep 7 hours, moderate stress..."
            className="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
          />
        </Card>
      )}

      {/* Step 4: Review */}
      {step === 4 && (
        <Card>
          <h3 className="text-lg font-semibold text-slate-900 mb-6">Review Your Information</h3>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="bg-slate-50 p-3 rounded-lg"><span className="text-slate-500">Age:</span> <span className="font-medium">{form.age}</span></div>
              <div className="bg-slate-50 p-3 rounded-lg"><span className="text-slate-500">Sex:</span> <span className="font-medium">{form.sex}</span></div>
              <div className="bg-slate-50 p-3 rounded-lg"><span className="text-slate-500">Chest Pain:</span> <span className="font-medium">{chestPainTypes.find(o => o.value === Number(form.chest_pain_type))?.label}</span></div>
              <div className="bg-slate-50 p-3 rounded-lg"><span className="text-slate-500">BP:</span> <span className="font-medium">{form.resting_blood_pressure} mmHg</span></div>
              <div className="bg-slate-50 p-3 rounded-lg"><span className="text-slate-500">Cholesterol:</span> <span className="font-medium">{form.cholesterol} mg/dl</span></div>
              <div className="bg-slate-50 p-3 rounded-lg"><span className="text-slate-500">Max HR:</span> <span className="font-medium">{form.max_heart_rate}</span></div>
              <div className="bg-slate-50 p-3 rounded-lg"><span className="text-slate-500">ST Depression:</span> <span className="font-medium">{form.st_depression}</span></div>
              <div className="bg-slate-50 p-3 rounded-lg"><span className="text-slate-500">Major Vessels:</span> <span className="font-medium">{form.num_major_vessels}</span></div>
            </div>
            {form.lifestyle_text && (
              <div className="bg-slate-50 p-3 rounded-lg text-sm">
                <span className="text-slate-500">Lifestyle:</span>
                <p className="mt-1 text-slate-700">{form.lifestyle_text}</p>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Navigation */}
      <div className="flex items-center justify-between mt-6">
        {step > 1 ? (
          <Button variant="secondary" onClick={prev}><ChevronLeft className="h-4 w-4" /> Previous</Button>
        ) : <div />}
        {step < 4 ? (
          <Button onClick={next}>Next <ChevronRight className="h-4 w-4" /></Button>
        ) : (
          <Button loading={loading} onClick={handleSubmit}>Submit Assessment</Button>
        )}
      </div>
    </div>
  )
}

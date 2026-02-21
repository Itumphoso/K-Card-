import React from 'react';
import { SafeAreaView, View, Text, TextInput, TouchableOpacity, ScrollView } from 'react-native';

const bg = '#0B1B3A';
const card = { backgroundColor: '#173567', borderRadius: 18, padding: 16, marginBottom: 12 };

export default function App() {
  return <SafeAreaView style={{ flex: 1, backgroundColor: bg }}><ScrollView contentContainerStyle={{ padding: 20 }}>
    <Text style={{ color: '#fff', fontSize: 28, textAlign: 'center', marginTop: 30 }}>K-Card</Text>
    <Text style={{ color: '#c8d8ff', textAlign: 'center', marginBottom: 24 }}>Welcome back</Text>
    <TextInput placeholder='Email' placeholderTextColor='#9fb1d8' style={{ ...card, color: '#fff' }} />
    <TextInput placeholder='Password' placeholderTextColor='#9fb1d8' secureTextEntry style={{ ...card, color: '#fff' }} />
    <TouchableOpacity style={{ backgroundColor: '#4F8CFF', borderRadius: 18, padding: 16, marginBottom: 20 }}><Text style={{ color: '#fff', textAlign: 'center', fontWeight: '700' }}>Login</Text></TouchableOpacity>
    <View style={{ flexDirection: 'row', gap: 12 }}><View style={{ ...card, flex: 1 }}><Text style={{ color: '#fff' }}>Generate QR</Text></View><View style={{ ...card, flex: 1 }}><Text style={{ color: '#fff' }}>Pay</Text></View></View>
    {['Balance Card','History','Top Up (M-Pesa / EcoCash / Card)','Rewards','Find Cabs'].map((t)=><View key={t} style={card}><Text style={{color:'#fff'}}>{t}</Text></View>)}
  </ScrollView></SafeAreaView>;
}
